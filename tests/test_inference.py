from app.inference import service


def test_prediction_returns_valid_structure():
    payload = {
        "income": 45000,
        "age": 29,
        "debt_ratio": 0.32,
        "credit_score": 690,
        "loan_amount": 12000,
        "employment_years": 3,
    }

    result = service.predict(payload)

    assert "probability" in result
    assert "label" in result
    assert "model_version" in result
    assert "threshold" in result
    assert 0.0 <= result["probability"] <= 1.0
    assert result["label"] in (0, 1)

