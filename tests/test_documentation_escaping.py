def test_comment_cannot_close_docstring() -> None:
    # Importing the module would raise if a comment had escaped the docstring.
    from .output_betterproto.documentation_escaping import Test

    assert Test.__doc__ is not None
    assert '"""; raise RuntimeError("comment escaped the docstring"); """' in Test.__doc__
    assert 'A "quoted" word, a trailing quote" and a backslash \\ in a comment.' in Test.__doc__
