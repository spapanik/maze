from unittest import mock

from maze.__main__ import main


@mock.patch(
    "maze.__main__.parse_args",
    new=mock.MagicMock(return_value=mock.MagicMock(rows=14, columns=9)),
)
@mock.patch("maze.__main__.play")
def test_clone(mock_play: mock.MagicMock) -> None:
    main()
    assert mock_play.call_count == 1
    calls = [mock.call(14, 9)]
    assert mock_play.call_args_list == calls
