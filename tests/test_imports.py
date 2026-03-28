"""Import sanity checks for the scaffold."""


def test_package_imports() -> None:
    import agent_design_studio
    from agent_design_studio.schemas import DesignDoc, DesignState, TradeoffSpec

    assert agent_design_studio.__version__ == "0.1.0"
    assert DesignDoc is not None
    assert DesignState is not None
    assert TradeoffSpec is not None

