# Deploying a Grading Service

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

## Step-by-Step Deployments

This section provides step-by-step deployment instructions for deploying an Otter Service instance on different cloud providers.

### Azure
