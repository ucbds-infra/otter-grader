# Grading on a Deployable Service

Otter Service is a deployable grading server that students can send submissions to from in the notebook and which will grade submissions based on predefined tests. It is a service packaged with Otter but has additional requirements that are not necessary for running Otter without Otter Service. Otter Service is a tornado server that accepts requests with student submissions, writes the submission to disk, grades them, and saves the grade breakdowns in a Postgres database. This page details how to configure an already-deployed Otter Service instance, and is agnostic of deployment type. For more information on deploying an Otter Service instance, see [below](#deploying-a-grading-service). 

## Configuration Repo

Otter Service is configured to grade assignments through a repository structure. While maintaing a git repo of assignment configurations is not required, it certainly makes editing and updated your assignments easier. Any directory that has the structure described here will do to set up assignments on an Otter Service deployments. If you are grading multiple classes on an Otter Service deployment, you must have one assignments repo for **each** class.

The first and most important file required is the `conf.yml` file, at the root of the repo. This file will define some important configurations and provide paths to the necessary files for each assignment. While the following structure is not required, we recommend something like it to keep a logical structure to the repo.

```
| data-8-assignments
    | - conf.yml
    | - requirements.txt
    | hw
        | hw01
            | - requirements.txt
            | test
                | - q0.py
                | - q1.py
                ...
        | hw02
        ...
    | proj
        | proj01
        ...
    ...
```

### The Configuration File

The `conf.yml` file is a YAML-formatted file that defines the necessary configurations and paths to set up assignments on an Otter Service deployment. It has the following structure:

```yaml
class_name: Data 8      # the name of the course
class_id: data8x        # a **unique** ID for the course
requirements: requirements.txt      # Path to a **global** reuquirements file
assignments:                        # list of assignments
    - name: Project 2               # assignment name
      assignment_id: proj02         # assignment ID, unique among all assignments in this config
      tests_path: proj/proj02/tests                     # path to directory of tests for this assignment
      requirements: proj/proj02/requirements.txt        # path to requirements specific to **this** assignment
      seed: 42                      # random seed for intercell seeding
      files:                        # list of files needed by the autograder, e.g. data files
        - proj/proj02/frontiers1.csv
        - proj/proj02/frontiers2.csv
        - proj/proj02/players.py
    ...
```

Note that the `class_id` must be unique among **all** classes being run on the Otter Service instance, whereas the `assignment_id`s must be unique only within a specific class. Also note that there are two requirements files: a global requirements file that contains requirements not [already in the Docker image](otter_grade.html#requirements) to be installed on **all** assignment images in this config, and an assignment-specific requirements file to be installed **only** in the image for that assignment. Also note that all paths are relative to the root of the assignments repo.

### Other Files

Other files can be included basically anywhere as long as its a subdirectory of the assignments repo, as long as their paths are specified in the `conf.yml` file. The assignments repo should contain any necessary requirements files, all test files, and any support files needed to execute the notebooks (e.g. data files, Python scripts).

## Building the Images

Once you have cloned your assignments repo onto your Otter Service deployment, use the command `otter service build` to add assignments to the database and create their Docker images. Note that it is often necessary to run `otter service build` with `sudo` so that you have the necessary permissions; in this section, assume that we have prepended each command with `sudo -E`.

The builder takes one positional argument that corresponds to the path to the assignments repo; this is assumed to be `./` (i.e. it is assumed to be the working directory). It also has four arguments corresponding to Posgres connection information (the host, port, username, and password which default to `localhost`, `5432`, `root`, and `root`, resp.), an optional `--image` flag to change out the base image for the Docker images (defaults to `ucbdsinfra/otter-grader`), and quiet `-q` flag to stop Docker from printing to the console on building the images.

From the root of the assignments repo, building couldn't be simpler:

```
otter service build
```

This command will add all assignments in the `conf.yml` to the database and create the needed Docker images to grade submissions. Images will be tagged as `{CLASS ID}-{ASSIGNMENT ID}` from the `conf.yml` file. So the first assignment in the example above would be tagged `data8x-proj02`.

## Running the Service

Once you have run `otter service build`, you are ready to start the service instance listening for requests. To do this, run `otter service start`, which takes an optional `--port` flag that indicates the port to listen on (this defaults to 80, the HTTP port). When a student submits, their submission is written to the disk and a job to grade the assignment is sent to a `concurrent.futures.ThreadPoolExecutor`. Once grading is finished, the database entry for that submission is updated with the score and the stdout and stderr of the grading process are written to text files in the submission directory. A submission is written to the following path:

```
/otter-service/submissions/class-{CLASS ID}/assignment-{ASSIGNMENT ID}/submission-{SUBMISSION ID}/{ASSIGNMENT NAME}.ipynb
```

To start Otter Service, run

```
$ otter service start
Listening on port 80
```

If you need to run Otter Service in the background, e.g. so you can log out of your SSH session, we recommend using [screen](https://linuxize.com/post/how-to-use-linux-screen/) to run the process in a separate session.

## Interacting with the Database

In setting up your Otter Service deployment, a Postgres database called `otter_db` was created to hold information about classes, assignments, and scores. The database has the following schema:

```sql
CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    api_keys VARCHAR[] CHECK (cardinality(api_keys) > 0),
    username TEXT UNIQUE,
    password VARCHAR,
    email TEXT UNIQUE,
    CONSTRAINT has_username_or_email CHECK (username IS NOT NULL or email IS NOT NULL)
)

CREATE TABLE classes (
    class_id TEXT PRIMARY KEY,
    class_name TEXT NOT NULL
)

CREATE TABLE assignments (
    assignment_id TEXT NOT NULL,
    class_id TEXT REFERENCES classes (class_id) NOT NULL,
    assignment_name TEXT NOT NULL,
    seed INTEGER,
    PRIMARY KEY (assignment_id, class_id)
)

CREATE TABLE submissions (
    submission_id SERIAL PRIMARY KEY,
    assignment_id TEXT NOT NULL,
    class_id TEXT NOT NULL,
    user_id INTEGER REFERENCES users(user_id) NOT NULL,
    file_path TEXT NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    score JSONB,
    FOREIGN KEY (assignment_id, class_id) REFERENCES assignments (assignment_id, class_id)
)
```

The above tables encompass all of the information that Otter Service stores. When a student sends a POST request with their submission, the submission is logged in the `submissions` table with a null `score`. Once grading finishes, the `score` for that submission is filled in as a JSON object that maps question identifiers to scores by question.

## Deploying a Grading Service

This section describes how to deploy an Otter Service instance. For more information on how to use an already-deployed service, see [Grading on a Deployed Service](otter_service.md).

### VM Requirements

Otter Service instances can be deployed as virtual machines on the cloud provider of your choice. We recommend using Debian as the OS on your VM. To use Otter Service, the VM requires the following to be installed:

* Postgres
* Python 3.6+ (and pip3)
* Docker
* [Otter's Python requirements](https://github.com/ucbds-infra/otter-grader/blob/master/requirements.txt)

Once you have installed the necessary requirements, you need to create a Postgres user that Otter can use to interact with the database. We recommend, and Otter defaults to, the username `root` with password `root`. 

```
sudo -u postgres bash
createuser -dP root       # enter password 'root' when prompted
```

Now that there is a `root` user, the database can be created:

```
sudo -E otter service create
```

`otter service create` creates the Postgres database `otter_db`, if it does not already exist, with the following relations:

```sql
CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    api_keys VARCHAR[] CHECK (cardinality(api_keys) > 0),
    username TEXT UNIQUE,
    password VARCHAR,
    email TEXT UNIQUE,
    CONSTRAINT has_username_or_email CHECK (username IS NOT NULL or email IS NOT NULL)
)

CREATE TABLE classes (
    class_id TEXT PRIMARY KEY,
    class_name TEXT NOT NULL
)

CREATE TABLE assignments (
    assignment_id TEXT NOT NULL,
    class_id TEXT REFERENCES classes (class_id) NOT NULL,
    assignment_name TEXT NOT NULL,
    seed INTEGER,
    PRIMARY KEY (assignment_id, class_id)
)

CREATE TABLE submissions (
    submission_id SERIAL PRIMARY KEY,
    assignment_id TEXT NOT NULL,
    class_id TEXT NOT NULL,
    user_id INTEGER REFERENCES users(user_id) NOT NULL,
    file_path TEXT NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    score JSONB,
    FOREIGN KEY (assignment_id, class_id) REFERENCES assignments (assignment_id, class_id)
)
```

Now Otter needs a few environment variables set. We recommend that you put this in _your_ `.bashrc` and then call Otter using `sudo -E` to maintain your environment. The environment variables needed are detailed below.

| Variable | Description |
|-----|-----|
| `GOOGLE_CLIENT_KEY` | A client ID from Google for Google OAuth |
| `GOOGLE_CLIENT_SECRET` | A client secret from Google for Google OAuth |
| `OTTER_ENDPOINT` | The base URL of this VM |

This can be done by appending something like the following to `~/.bashrc`:

```bash
export GOOGLE_CLIENT_KEY="someKey1234.apps.googleusercontent.com"
export GOOGLE_CLIENT_SECRET="someSecret5678"
export OTTER_ENDPOINT="http://my-otter-service-instance.westus.cloudapp.azure.com"
```

Finally, the last thing to do is allow inbound traffic on port 80 (or whatever port you pass to the `--port` flag of `otter service start`). This will allow requests to be sent to the VM for grading.

Now that you have set up your VM, you're ready to start [grading with it](otter_service.md).

### Step-by-Step Deployment Instructions

This section provides step-by-step deployment instructions for deploying an Otter Service instance on different cloud providers.

#### Azure

To start deploying an Otter Service VM on Azure, first create a resource group and subscription to house your VM. Then create a new VM from the Virtual Machines menu on the Azure portal. We recommend the `Debian 10 "Buster"` image. The recommended size parameters (`Standard D2s v3 2 vcpus, 8 GiB memory`) are good for a smaller course (< 50 students), but you can scale up the memory for larger courses. You should also provide your [SSH public key](https://docs.microsoft.com/en-us/azure/virtual-machines/linux/mac-create-ssh-keys) so that you can SSH into the VM to set it up. You will need the SSH and HTTP ports open so that you can configure the VM and so that it can accept requests.

![](images/service_vm_ports.png)

The other default configuations are fine, so select "Review + Create", double check the details, and click "Create" to create the VM. Once your deployment has finished, you will need to change the public IP address from dynamic to static and secure a DNS name label. To do this, click "Configure" next to **DNS name** on the Overview page.

![](images/service_configure_dns.png)

On this page, set **Assignment** to "Static" and create a DNS name label in the **DNS name label** field for your VM. The latter is very important because Google Cloud will not let you use an IP address when creating your OAuth credentials. Click **Save** at the top to save these changes.

![](images/service_ip_address.png)

Continue setup by SSHing into the VM from your Terminal (more info on how to do this under **Connect** > **SSH**). Run the following commands to install Postgres, pip3, Docker, and Otter and its Python requirements.

```
sudo apt update
sudo apt-get update
sudo apt install -y postgresql postgresql-client python3-pip git python-psycopg2 libpq-dev nano
sudo apt-get -y install \
        apt-transport-https \
        ca-certificates \
        curl \
        gnupg-agent \
        software-properties-common
curl -fsSL https://download.docker.com/linux/debian/gpg | sudo apt-key add -
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io
sudo pip3 install git+https://github.com/ucbds-infra/otter-grader.git@beta
sudo pip3 install -r https://raw.githubusercontent.com/ucbds-infra/otter-grader/beta/requirements.txt
```

Once the above have run successfully, you need to create a Postgres user that Otter can use to create and manage it database. We recommend a user with username `root` and password `root` as these are the values that Otter defaults to.

```
$ sudo -u postgres bash
$ createuser -dP root
Password: 
```

At the `Password:` prompt, type the user password. 

Next, you will need to create a Google Cloud Platform project to use for Google OAuth. Once you have created the project, go to **APIs & Services** > **OAuth consent screen** and create one. You will need to add the DNS name you configured on Azure to the Authorized domains list. Click **Save** then go to **APIs & Services** > **Credentials** and click "+ Create Credentials" a the top and select "OAuth Client ID". Set the application type to "Web application" and add `http://{YOUR DNS NAME}/auth/callback` to the list of authorized redirect URIs. Click "Create".

![](images/service_create_oauth_id.png)

Google will provide you with a client ID and client secret; copy these down and SSH back into your VM. Use nano (or your preferred text editor) to open `~/.bashrc` and add the following to the end of it, filling in the values with the corresponding values.

```bash
export GOOGLE_CLIENT_KEY="{YOUR GOOGLE CLIENT ID}"
export GOOGLE_CLIENT_SECRET="{YOUR GOOGLE CLIENT SECRET}"
export OTTER_ENDPOINT="{YOUR DNS NAME}"
```

Now `source` your .bashrc file and create the Postgres database for Otter with

```
sudo -E otter service create
```

Congrats, that's all the setup! You're ready to start grading with Otter Service, as described [here](otter_service.md).

## Otter Service Reference

### `otter service build`

```eval_rst
.. argparse::
   :module: otter.argparser
   :func: get_parser
   :prog: otter
   :path: service build
   :nodefaultconst:
```

### `otter service create`

```eval_rst
.. argparse::
   :module: otter.argparser
   :func: get_parser
   :prog: otter
   :path: service create
   :nodefaultconst:
```

### `otter service start`

```eval_rst
.. argparse::
   :module: otter.argparser
   :func: get_parser
   :prog: otter
   :path: service start
   :nodefaultconst:
```
