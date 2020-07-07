class Question:
    """
    """

def find_question_spec(source):
    """Return line number of the BEGIN QUESTION line or None
    
    Args:
        source (``list`` of ``str``): cell source as a list of lines of text
    
    Returns:
        ``int``: line number of BEGIN QUESTION, if present
        ``None``: if BEGIN QUESTION not present in the cell
    """
    block_quotes = [i for i, line in enumerate(source) if
                    line[:3] == BLOCK_QUOTE]
    assert len(block_quotes) % 2 == 0, 'cannot parse ' + str(source)
    begins = [block_quotes[i] + 1 for i in range(0, len(block_quotes), 2) if
              source[block_quotes[i]+1].strip(' ') == 'BEGIN QUESTION']
    assert len(begins) <= 1, 'multiple questions defined in ' + str(source)
    return begins[0] if begins else None

def is_question_cell(cell):
    """Whether cell contains BEGIN QUESTION in a block quote
    
    Args:
        cell (``nbformat.NotebookNode``): notebook cell
    
    Returns:
        ``bool``: whether the current cell is a question definition cell

    """
    if cell['cell_type'] != 'markdown':
        return False
    return find_question_spec(get_source(cell)) is not None

def gen_question_cell(cell, manual, format, need_close_export):
    """Return a locked question cell with metadata hidden in an HTML comment
    
    Args:
        cell (``nbformat.NotebookNode``): the original question cell
    
    Returns:
        ``nbformat.NotebookNode``: the updated question cell
    """
    cell = copy.deepcopy(cell)
    source = get_source(cell)
    if manual:
        source = ["<!-- BEGIN QUESTION -->", ""] + source
    if need_close_export:
        source = ["<!-- END QUESTION -->", ""] + source
    begin_question_line = find_question_spec(source)
    start = begin_question_line - 1
    assert source[start].strip() == BLOCK_QUOTE
    end = begin_question_line
    while source[end].strip() != BLOCK_QUOTE:
        end += 1
    source[start] = "<!--"
    source[end] = "-->"
    cell['source'] = '\n'.join(source)

    # checkf or empty cell
    cell_text = source[:start]
    try:
        cell_text += source[end+1:]
    except IndexError:
        pass
    if not "".join(cell_text).strip():
        raise EmptyCellException()

    lock(cell)
    return cell

def read_question_metadata(cell):
    """Return question metadata from a question cell
    
    Args:
        cell (``nbformat.NotebookNode``): the question cell
    
    Returns:
        ``dict``: question metadata
    """
    source = get_source(cell)
    begin_question_line = find_question_spec(source)
    i, lines = begin_question_line + 1, []
    while source[i].strip() != BLOCK_QUOTE:
        lines.append(source[i])
        i = i + 1
    metadata = yaml.full_load('\n'.join(lines))
    assert ALLOWED_NAME.match(metadata.get('name', '')), metadata
    return metadata
