# Temperature in LLMs
*Course: AI Fundamentals*
Presenter: Professor Dr. Raju

---

# Objectives
- Define temperature and its role in LLM output generation
- Explain how temperature controls randomness and diversity
- Demonstrate practical effects on text quality and coherence
- Identify appropriate temperature settings for different use cases

---

# Definition
> Temperature is a hyperparameter that controls the randomness of token probabilities in LLM decoding by scaling the logits before softmax.
- Lower values make the model more deterministic and focused
- Higher values increase diversity but can reduce coherence

---

# Core Concepts
- **Softmax Scaling**: Logits are divided by temperature before applying softmax to adjust probability distribution
- **Sampling Strategy**: Temperature modifies probability weights used during nucleus or top‑k sampling
- **Output Variability**: Small temperature changes can significantly alter generated text style and content

---

# How It Works
- **Step 1 – Compute Logits**: Model produces raw logits for each token in the vocabulary
- **Step 2 – Scale by Temperature**: Each logit is divided by temperature before softmax conversion
- **Step 3 – Sample Token**: Token is sampled from the adjusted probability distribution

---

# Code Example
```python
import numpy as np

def sample_with_temperature(logits, temperature):
    """
    Sample a token index from a probability distribution
    derived from logits scaled by temperature.
    """
    scaled_logits = np.array(logits) / temperature
    exp_values = np.exp(scaled_logits - np.max(scaled_logits))
    probabilities = exp_values / exp_values.sum()
    token_index = np.random.choice(len(logits), p=probabilities)
    return token_index

# Example usage
logits = [2.0, 1.0, 0.1]
temperature = 0.7
chosen = sample_with_temperature(logits, temperature)
print(f"Sampled token index: {chosen}")
```

---

# Use Cases
- **Creative Writing**: Moderate to high temperature introduces variability and originality
- **Factual QA**: Low temperature ensures accurate and consistent responses
- **Dialog Systems**: Adaptive temperature balances coherence and engagement

---

# Comparison
| Variant | Pros | Cons |
|---------|------|------|
| Low Temperature (0.2) | Stable, focused output | Repetitive, less creative |
| Medium Temperature (0.7) | Balanced quality and diversity | Requires tuning for context |
| High Temperature (1.2) | Rich variation, creativity | Incoherent or off-topic outputs |

---

# Common Mistakes
- **Mistake**: Using high temperature for factual tasks → **Fix**: Set temperature below 0.5 to prioritize correctness
- **Mistake**: Applying extreme low temperature continuously → **Fix**: Vary temperature based on task and desired creativity
- **Mistake**: Ignoring interaction with top‑k or nucleus sampling → **Fix**: Combine temperature with other sampling controls thoughtfully

---

# Summary
- Temperature modulates the randomness of token selection in LLM decoding
- Low temperature favors precision; high temperature favors diversity
- Proper tuning depends on task requirements and desired output quality

---

# Questions?