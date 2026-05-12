from app.services.evaluator import GroundTruthEntity, compare_predictions
from app.services.gliner_runner import Prediction


def test_compare_predictions_counts_exact_text_and_label_matches() -> None:
    predictions = [
        Prediction(
            text="jane@example.com",
            label="email",
            taxonomy_label="EMAIL_ADDRESS",
            start=10,
            end=26,
            score=0.99,
        )
    ]
    ground_truth = [GroundTruthEntity(text="jane@example.com", label="EMAIL_ADDRESS")]

    result = compare_predictions(predictions, ground_truth)

    assert result.metrics["true_positives"] == 1
    assert result.metrics["false_positives"] == 0
    assert result.metrics["false_negatives"] == 0
    assert result.metrics["precision"] == 1
    assert result.metrics["recall"] == 1


def test_compare_predictions_tracks_false_negatives() -> None:
    result = compare_predictions(
        predictions=[],
        ground_truth=[GroundTruthEntity(text="Jane Smith", label="PERSON_NAME")],
    )

    assert result.metrics["true_positives"] == 0
    assert result.metrics["false_positives"] == 0
    assert result.metrics["false_negatives"] == 1
    assert result.matches[0]["status"] == "false_negative"

