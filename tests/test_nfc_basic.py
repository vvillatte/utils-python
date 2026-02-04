def test_import():
    import nfc_helper

    assert hasattr(nfc_helper, "main")