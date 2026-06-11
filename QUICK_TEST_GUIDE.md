# Quick Test Guide - yFinance API Updates

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install vaderSentiment pytest pytest-cov requests
```

### 2. Start the API Server
```bash
uvicorn app.main:app --reload --port 8000
```

### 3. Quick Manual Tests

#### Test Buzz Endpoint
```bash
curl http://localhost:8000/buzz/AAPL
```

**Expected Response:**
```json
{
  "symbol": "AAPL",
  "buzz": {
    "news_articles": 25,
    "total_mentions": 25,
    "attention_level": "moderate",
    "interpretation": "Stock is receiving moderate attention in the news"
  }
}
```

#### Test Sentiment Analysis
```bash
curl "http://localhost:8000/news/AAPL?limit=5"
```

**Expected Response:**
```json
{
  "symbol": "AAPL",
  "count": 5,
  "sentiment_summary": {
    "avg_compound": 0.1234,
    "positive_count": 3,
    "negative_count": 1,
    "neutral_count": 1,
    "positive_pct": 60.0,
    "negative_pct": 20.0,
    "bullish_ratio": 0.75,
    "overall_label": "positive"
  },
  "articles": [
    {
      "headline": "Apple announces...",
      "sentiment": {
        "compound": 0.8516,
        "positive": 0.432,
        "negative": 0.0,
        "neutral": 0.568,
        "label": "positive"
      }
    }
  ]
}
```

#### Test Extended Indicators
```bash
curl "http://localhost:8000/indicators/AAPL?tail=5"
```

**Expected Response:**
```json
{
  "symbol": "AAPL",
  "as_of": "2026-06-07",
  "current_price": 185.42,
  "rsi_14": [...],
  "macd": [...],
  "bollinger_bands_20": [...],
  "adx_14": [...],
  "atr_14": [...],
  "sma_50": [...],
  "cci_20": [...],
  "stochastic_14": [...],
  "obv": [...],
  "vwap": [...],
  "ema_20": [...]
}
```

---

## 🧪 Automated Test Execution

### Run All New Tests
```bash
pytest .slingshot/skills/test_examples/ -v
```

### Run Specific Test Files
```bash
# Buzz endpoint tests
pytest .slingshot/skills/test_examples/test_buzz.py -v

# Sentiment analysis tests
pytest .slingshot/skills/test_examples/test_sentiment.py -v

# Extended indicators tests
pytest .slingshot/skills/test_examples/test_indicators_extended.py -v
```

### Run with Coverage Report
```bash
pytest .slingshot/skills/test_examples/ --cov=app --cov-report=term --cov-report=html
```

---

## ✅ Validation Checklist

### Buzz Endpoint:
- [ ] Returns 200 status code
- [ ] Symbol is uppercase
- [ ] `news_articles` count is non-negative
- [ ] `attention_level` is one of: "low", "moderate", "high"
- [ ] Attention level matches article count thresholds:
  - High: ≥ 40 articles
  - Moderate: 15-39 articles
  - Low: < 15 articles
- [ ] `interpretation` text is present and meaningful
- [ ] Response time < 10 seconds

### Sentiment Analysis:
- [ ] Each article has `sentiment` object
- [ ] `compound` score in range [-1, 1]
- [ ] `positive`, `negative`, `neutral` scores in range [0, 1]
- [ ] `label` is one of: "positive", "negative", "neutral"
- [ ] Label matches compound score:
  - Positive: compound ≥ 0.05
  - Negative: compound ≤ -0.05
  - Neutral: -0.05 < compound < 0.05
- [ ] `sentiment_summary` is present
- [ ] Counts sum to total articles
- [ ] Percentages are valid (0-100)
- [ ] `bullish_ratio` in range [0, 1] when defined

### Extended Indicators:
- [ ] All 11 indicators are present in response
- [ ] RSI values in range [0, 100]
- [ ] ADX values in range [0, 100]
- [ ] Stochastic %K and %D in range [0, 100]
- [ ] Bollinger Bands: upper ≥ middle ≥ lower
- [ ] MACD has `macd`, `signal`, `histogram` fields
- [ ] ATR, SMA-50, VWAP, EMA-20 are positive
- [ ] CCI values are reasonable (-500 to +500)
- [ ] OBV is present (can be any value)
- [ ] `tail` parameter is respected (max data points)
- [ ] Response time < 15 seconds

---

## 🐛 Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'vaderSentiment'"
**Solution:**
```bash
pip install vaderSentiment
```

### Issue: "Connection refused" when testing
**Solution:**
```bash
# Ensure server is running
uvicorn app.main:app --reload --port 8000
```

### Issue: Tests fail with import errors
**Solution:**
```bash
# Set PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"  # Linux/Mac
set PYTHONPATH=%PYTHONPATH%;%CD%          # Windows CMD
$env:PYTHONPATH="$env:PYTHONPATH;$(pwd)"  # Windows PowerShell
```

### Issue: Slow indicator response times
**Solution:**
- Reduce `tail` parameter (default is 15)
- Use caching for repeated requests
- Consider upgrading server resources

---

## 📊 Expected Test Results

### test_buzz.py (9 tests)
```
test_buzz_valid_ticker                      PASSED
test_buzz_multiple_tickers[AAPL]            PASSED
test_buzz_multiple_tickers[MSFT]            PASSED
test_buzz_attention_level_logic             PASSED
test_buzz_interpretation_field              PASSED
test_buzz_total_mentions_equals_articles    PASSED
test_buzz_invalid_ticker                    PASSED
test_buzz_with_api_key                      PASSED
test_buzz_response_time                     PASSED
```

### test_sentiment.py (12 tests)
```
test_news_sentiment_structure               PASSED
test_sentiment_compound_range               PASSED
test_sentiment_component_scores_range       PASSED
test_sentiment_label_logic                  PASSED
test_sentiment_summary_structure            PASSED
test_sentiment_summary_counts               PASSED
test_sentiment_summary_percentages          PASSED
test_sentiment_bullish_ratio                PASSED
test_sentiment_overall_label                PASSED
test_sentiment_empty_news                   PASSED
test_sentiment_various_sample_sizes[5]      PASSED
test_sentiment_various_sample_sizes[10]     PASSED
```

### test_indicators_extended.py (17 tests)
```
test_all_indicators_present                 PASSED
test_rsi_range                              PASSED
test_macd_structure                         PASSED
test_bollinger_bands_structure              PASSED
test_bollinger_bands_relationship           PASSED
test_adx_range                              PASSED
test_atr_positive                           PASSED
test_sma_50_positive                        PASSED
test_cci_typical_range                      PASSED
test_stochastic_structure                   PASSED
test_stochastic_range                       PASSED
test_obv_trend                              PASSED
test_vwap_positive                          PASSED
test_ema_20_positive                        PASSED
test_current_price_present                  PASSED
test_as_of_date_present                     PASSED
test_all_indicators_performance             PASSED
```

**Total: 38 new tests, all should PASS ✅**

---

## 🎯 Success Criteria

✅ **Implementation Complete** when:
1. All 3 new test files pass without errors
2. Manual curl tests return expected JSON structures
3. Sentiment scores are in valid ranges
4. Buzz attention levels match thresholds
5. All 11 indicators are present in response
6. Response times meet performance benchmarks

---

## 📝 Next Actions

1. ✅ Run quick manual tests with curl
2. ✅ Execute automated test suite
3. ✅ Verify all tests pass
4. ✅ Check performance benchmarks
5. ✅ Deploy to staging/production
6. ✅ Update API documentation
7. ✅ Notify stakeholders of new features

**Happy Testing! 🚀**
