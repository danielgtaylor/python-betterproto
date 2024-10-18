import ast
import inspect


def test_documentation():
    from .output_betterproto.documentation import Enum, Test, ServiceBase, ServiceStub

    assert Test.__doc__ == "Documentation of message"

    source = inspect.getsource(Test)
    tree = ast.parse(source)
    assert tree.body[0].body[2].value.value == "Documentation of field"

    assert Enum.__doc__ == "Documentation of enum"

    source = inspect.getsource(Enum)
    tree = ast.parse(source)
    assert tree.body[0].body[2].value.value == "Documentation of variant"

    assert ServiceBase.__doc__ == "Documentation of service"
    assert ServiceBase.get.__doc__ == "Documentation of method"

    assert ServiceStub.__doc__ == "Documentation of service"
    assert ServiceStub.get.__doc__ == "Documentation of method"
