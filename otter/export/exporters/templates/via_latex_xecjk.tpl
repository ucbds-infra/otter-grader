% Default to the notebook output style
((* if not cell_style is defined *))
    ((* set cell_style = 'style_ipython.tplx' *))
((* endif *))

% Inherit from the specified cell style.
((* extends cell_style *))


%===============================================================================
% Latex Article
%===============================================================================

((* block docclass *))
\documentclass[10pt]{article}
\newcommand\cleartooddpage{\clearpage
	\ifodd\value{page}\else\null\clearpage\fi}
\date\today
\renewcommand{\linethickness}{0.05em}
\setlength{\parskip}{2em}
\setlength{\parindent}{0em}

\usepackage{xeCJK}

((* endblock docclass *))

((* block maketitle *))
((* endblock maketitle *))

((* block markdowncell scoped *))
        ((*- if cell.source and "#newpage" in cell.source-*))
		\cleartooddpage
        ((*- endif -*))
((( super() )))
((* endblock markdowncell *))

