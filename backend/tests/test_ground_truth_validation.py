import pandas as pd
import pytest

from app.services.evaluator import validate_ground_truth_frame


def test_validate_ground_truth_frame_accepts_supported_column_names() -> None:
    frame = pd.DataFrame(
        {
            "entity_text": ["Jane Smith"],
            "entity_type": ["PERSON_NAME"],
        }
    )

    result = validate_ground_truth_frame(frame)

    assert result.text_column == "entity_text"
    assert result.label_column == "entity_type"
    assert result.row_count == 1


def test_validate_ground_truth_frame_rejects_missing_required_columns() -> None:
    frame = pd.DataFrame(
        {
            "page": [1],
            "start": [0],
            "end": [10],
        }
    )

    with pytest.raises(ValueError) as exc_info:
        validate_ground_truth_frame(frame)

    assert "Ground truth CSV must include a text column and a label column" in str(exc_info.value)
