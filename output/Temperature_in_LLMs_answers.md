# TA Answers: Temperature in LLMs

# Clarification Questions

## 1. If temperature is applied to logits before softmax, how does scaling by a value less than 1.0 make the distribution sharper? Could you walk through the math to show why dividing by a small temperature increases the exponent’s magnitude and concentrates probability mass?

**Answer:**  
Let's break down the math step by step. Recall the softmax formula with temperature:

\[
P(i) = \frac{e^{z_i / T}}{\sum_j e^{z_j / T}}
\]

where \(z_i\) are the logits and \(T\) is temperature.

- When \(T < 1\), dividing by \(T\) increases the magnitude of each logit: \(z_i / T > z_i\) (if \(z_i > 0\)).
- The exponential function \(e^x\) grows rapidly with \(x\). Larger logits become even larger after exponentiation, while smaller logits become even smaller (or very close to zero).
- For example, consider logits \([2.0, 1.0, 0.1]\) with \(T=0.5\):
  - Scaled logits: \([4.0, 2.0, 0.2]\)
  - Exponentiated: \([e^4, e^2, e^{0.2}] \approx [54.6, 7.39, 1.22]\)
  - The largest term dominates the sum, so \(P(i)\) for the largest logit approaches 1.

This amplifies differences between logits, concentrating probability mass on the highest logit. The subtraction of the max (for numerical stability) happens **after** scaling, i.e., we compute \(e^{(z_i / T) - \max(z/T)}\), which doesn't change the relative scaling—it only prevents overflow.

**Code illustration:**

```python
import numpy as np

def softmax_with_temp(logits, T):
    scaled = np.array(logits) / T
    shifted = scaled - np.max(scaled)  # for stability
    exp_vals = np.exp(shifted)
    return exp_vals / exp_vals.sum()

print("T=1.0:", softmax_with_temp([2.0, 1.0, 0.1], 1.0))
print("T=0.5:", softmax_with_temp([2.0, 1.0, 0.1], 0.5))
```

You’ll see that with \(T=0.5\), the probability for the first token becomes much larger (sharper distribution).

**Reference:** Slide 3 (Softmax Scaling) and Slide 4 (How It Works).

---

## 2. When we say temperature “controls randomness,” is this randomness solely about token probability distributions, or does it also interact with the deterministic argmax decoding in any way?

**Answer:**  
Temperature exclusively affects the **probability distribution** used during **sampling** (e.g., top‑k or nucleus sampling). It does not alter argmax (greedy) decoding, which simply picks the token with the highest probability regardless of temperature. However, by changing the probabilities, temperature indirectly influences which token is most likely to be selected in a deterministic sense: a very low temperature will make the highest-logit token overwhelmingly probable, so argmax and low-temperature sampling will often agree. But in high-temperature scenarios, sampling can pick sub‑max tokens more often, introducing randomness that argmax would never show.

Thus, randomness is a property of the sampling process, not of the model’s raw logits. If you always use argmax, temperature has no effect—highlighting why decoding strategy matters.

**Reference:** Slide 2 (Definition) and Slide 5 (Core Concepts).

---

## 3. The formula divides each logit by temperature before subtracting the max for numerical stability. Does the subtraction of max happen before or after scaling by temperature, and does the order affect the final probabilities?

**Answer:**  
The subtraction of the max (shift) happens **after** scaling by temperature. In the code:

1. `scaled_logits = np.array(logits) / temperature`
2. `shifted = scaled_logits - np.max(scaled_logits)`
3. `exp_values = np.exp(shifted)`

Mathematically, this is equivalent to the standard stable softmax:

\[
\text{softmax}(z_i/T) = \frac{e^{z_i/T - \max(z/T)}}{\sum_j e^{z_j/T - \max(z/T)}}
\]

The order **does not affect** the final probabilities because subtracting a constant from all logits (after scaling) cancels out in the softmax ratio. This is a numerical trick to prevent overflow when exponents get large. If you subtracted the max **before** scaling, it would change the result (since \(\max(z)/T \neq \max(z/T)\) in terms of shifting), but we always scale first then shift.

**Reference:** Slide 7 (Code Example) and the softmax explanation.

---

## 4. In practice, how does temperature interact with model confidence? If the model already assigns a very high probability to a single token, will increasing temperature still meaningfully change the sampling outcome?

**Answer:**  
When the model is highly confident (one logit much larger than others), increasing temperature **reduces** that confidence by flattening the distribution. For example, logits \([10.0, 0.0, 0.0]\):

- At \(T=1\), the first token probability ≈ 0.99995.
- At \(T=2\), scaled logits become \([5.0, 0.0, 0.0]\), probabilities shift to ≈ 0.993.

So yes, temperature still changes outcomes—it makes the distribution more uniform. However, the effect is smaller in relative terms when the gap between logits is large. In extreme cases (e.g., logits differing by 20+), even high temperature may not cause noticeable diversity because the highest logit still dominates.

**Code demo:**

```python
import numpy as np

def prob_first(logits, T):
    scaled = np.array(logits) / T
    shifted = scaled - np.max(scaled)
    exp_vals = np.exp(shifted)
    return exp_vals[0] / exp_vals.sum()

print("T=1:", prob_first([10.0, 0.0, 0.0], 1.0))
print("T=2:", prob_first([10.0, 0.0, 0.0], 2.0))
print("T=5:", prob_first([10.0, 0.0, 0.0], 5.0))
```

You’ll see the probability decreases as T increases, but remains high.

**Reference:** Slide 6 (Low Temperature) and Slide 9 (Comparison).

---

## 5. The slides mention that small temperature changes can significantly alter generated text. Is this sensitivity consistent across different layers or heads in the model, or does it vary depending on which part of the network the temperature is applied to?

**Answer:**  
Temperature is applied **after** the model produces logits—typically at the final output layer before sampling. Its effect is on the token distribution, not on internal layers. Sensitivity to temperature varies by **context and token**, not by layer, because:
- Different prompts lead to different logit spreads.
- Some tokens have similar logits, so small temperature changes can flip their probabilities significantly (especially near the top of the distribution).
- In layers before the final output, temperature isn’t applied, so internal representations remain unaffected.

Thus, sensitivity is not uniform—it depends on how close the top logits are. If logits are very close (e.g., in ambiguous contexts), even tiny temperature changes can reorder probabilities dramatically.

**Reference:** Slide 5 (Core Concepts: Output Variability).

---

# Application Questions

## 6. For a customer support chatbot that needs to balance factual correctness with engaging responses, what concrete temperature adjustment strategy would you recommend for open-ended versus closed-ended user queries?

**Answer:**  
Use **adaptive temperature** based on query type:
- **Closed-ended queries** (e.g., "What is your return policy?"): Set temperature low (0.2–0.4) to prioritize factual accuracy and consistency.
- **Open-ended queries** (e.g., "Tell me about your day"): Use moderate to high temperature (0.7–1.0) to encourage creativity and engagement, while staying within guardrails.

You could implement a simple rule: if the intent is factual (detected via classifier), use low T; otherwise, use medium T. This balances correctness (Slide 11, Use Cases) with engagement (Slide 6, Medium Temperature).

**Reference:** Slide 11 (Use Cases) and Slide 12 (Comparison).

---

## 7. If you are generating long-form creative content with a high temperature but notice coherence drops, could you dynamically adjust temperature mid-generation (e.g., lower for critical sentences, higher for brainstorming phrases), and how would you decide the switching criteria?

**Answer:**  
Yes, dynamic temperature adjustment is effective. Strategies include:
- **Sentence-level switching:** Use high temperature for initial idea generation (e.g., first 20% of tokens), then lower temperature (0.3–0.5) for elaboration to improve coherence.
- **Confidence-based switching:** If the model’s top-token probability falls below a threshold (e.g., <0.3), reduce temperature to avoid drift.
- **Topic-shift detection:** When a new topic is detected (via keyword or embedding similarity), temporarily increase temperature for novelty, then stabilize.

**Example heuristic:**

```python
def dynamic_temp(token_idx, top_prob, prompt_len):
    if token_idx < prompt_len * 0.2:  # brainstorming phase
        return 1.0
    elif top_prob < 0.3:  # model is uncertain
        return 0.5
    else:
        return 0.7
```

This balances creativity (high T) with coherence (low T) as per Slide 12 and Slide 9.

**Reference:** Slide 11 (High Temperature) and Slide 9 (Comparison).

---

## 8. When fine-tuning an LLM for a domain-specific task like medical advice, should temperature be treated as a hyperparameter tuned during validation, or is it more effective to keep it fixed at a low value and adjust it only at inference time?

**Answer:**  
For domain-specific fine-tuning, **keep temperature fixed at a low value (e.g., 0.2–0.3)** and tune other hyperparameters (learning rate, batch size) during training. Temperature is primarily an **inference-time knob** for controlling output diversity, not a trainable parameter. Adjusting it post-training allows flexible deployment:
- Use low T for safety-critical domains (medical, legal) to ensure consistency.
- If needed, slightly increase T during inference for user-facing interactions to add helpful variability.

Tuning temperature during training (e.g., via RL) is complex and rarely done; it’s more practical to treat it as a deployment hyperparameter (Slide 13, Use Cases; Slide 14, Common Mistakes).

**Reference:** Slide 13 (Use Cases) and Slide 14 (Common Mistakes).

---

## 9. In a retrieval-augmented generation setup, how should temperature be set when combining retrieved passages with generated text to ensure consistency between the retrieved evidence and the model’s creative elaboration?

**Answer:**  
Use **two-stage temperature control**:
1. **Retrieved evidence integration:** Keep temperature low (0.2–0.4) when generating responses that heavily rely on retrieved facts to maintain fidelity.
2. **Creative elaboration:** Allow higher temperature (0.7–1.0) for generating explanations, examples, or transitions around the retrieved content.

Alternatively, use **context-aware temperature**: if the model’s confidence in retrieved passages is high (e.g., cosine similarity > threshold), lower temperature; otherwise, increase temperature to encourage the model to reinterpret the evidence.

This aligns with Slide 11 (Factual QA → low temp) and Slide 12 (Adaptive temperature).

**Reference:** Slide 11 (Use Cases) and Slide 12 (Adaptive Temperature).

---

## 10. Could you design a simple experiment to demonstrate the effect of temperature on output diversity for a given prompt, including metrics you would use to quantify diversity versus coherence?

**Answer:**  
**Experiment design:**
1. Fix a prompt (e.g., "Describe a futuristic city").
2. Generate 20 responses each at temperatures: 0.2, 0.7, 1.2.
3. Measure:
   - **Diversity:** Use distinct n‑gram counts or embedding cosine distance between responses.
   - **Coherence:** Use a language model score (e.g., perplexity) or a factuality classifier.
4. Plot diversity vs. coherence for each temperature.

**Expected outcome:**  
- T=0.2: Low diversity, high coherence.
- T=1.2: High diversity, lower coherence.
- T=0.7: Balanced.

**Code sketch:**

```python
import numpy as llm
# Assume generate(prompt, temperature) returns a string
def experiment(prompt):
    temps = [0.2, 0.7, 1.2]
    for T in temps:
        texts = [generate(prompt, T) for _ in range(20)]
        diversity = len(set(texts)) / len(texts)  # naive diversity
        coherence = np.mean([llm.perplexity(t) for t in texts])
        print(f"T={T}: diversity={diversity:.2f}, avg_coherence={coherence:.2f}")
```

**Reference:** Slide 9 (Comparison) and Slide 12 (Use Cases).

---

# Edge Case Questions

## 11. What happens if temperature is set to exactly 1.0 in the provided code—is this equivalent to leaving the logits unscaled, or does the subtraction of max in the exponent slightly alter the behavior compared to a “no temperature” baseline?

**Answer:**  
Temperature = 1.0 means **no scaling** of logits (since dividing by 1.0 does nothing). However, the **subtraction of max** still occurs for numerical stability. This shift does not affect probabilities because:

\[
\frac{e^{z_i - \max(z)}}{\sum_j e^{z_j - \max(z)}} = \frac{e^{z_i}}{\sum_j e^{z_j}}
\]

So with T=1.0, the result is **identical** to the standard softmax without any scaling or shift. The code is numerically stable but mathematically equivalent to “no temperature.”

**Reference:** Slide 7 (Code Example) and softmax properties.

---

## 12. If temperature is set to a very high value (e.g., 10.0), causing all logits to become nearly equal, will sampling still be meaningful, and does this scenario expose any numerical issues in the softmax computation?

**Answer:**  
At very high temperature (e.g., T=10), logits are heavily scaled down: \(z_i / T \approx 0\), making all exponentiated values ≈ 1. This leads to a **near-uniform distribution**, so sampling becomes almost random—potentially meaningless if you expect coherent outputs.

Numerically, this is safe: scaled logits are small, so exponentiation won’t overflow. However, **underflow** is possible if logits are very negative (e.g., -1000), but `exp(-1000)` underflows to 0, which is handled gracefully by floating-point arithmetic. The subtraction of max keeps values non-positive, preventing overflow.

**Practical note:** Extremely high temperatures may produce incoherent text, as noted in Slide 9 (High Temperature cons).

**Reference:** Slide 2 (High Temperature) and Slide 4 (How It Works).

---

## 13. In top‑k or nucleus sampling, can an extremely low temperature cause the probability mass to collapse onto tokens that may be excluded by the filtering steps, leading to empty or invalid candidate sets?

**Answer:**  
Yes, this is possible. With very low temperature, probability mass collapses onto the top logit(s). If those tokens are **excluded** by top‑k (k=1 is safe) or nucleus (p too small) filtering, the remaining candidates may have near-zero probability, causing:
- **Empty candidate sets** (if all top tokens are filtered), leading to errors.
- **Overly deterministic sampling** even when filtering is intended to restrict choices.

**Mitigation:** Ensure temperature is not too low when using filtering, or set k/p to include at least one high-probability token. For example, with top‑k=5, avoid T < 0.3 unless you know the top 5 logits are close in value.

**Reference:** Slide 5 (Sampling Strategy) and Slide 14 (Common Mistakes).

---

## 14. If logits contain very large positive or negative values (e.g., due to extreme model confidence), does temperature scaling interact with floating-point underflow/overflow risks differently than in the standard softmax implementation?

**Answer:**  
Temperature scaling **alters the risk profile**:
- **Large positive logits** (e.g., 1000): Without temperature, \(e^{1000}\) overflows. With low temperature (e.g., T=0.1), scaled logit becomes 10000—**worse overflow risk**.
- **Large negative logits** (e.g., -1000): With high temperature (e.g., T=2), scaled logit becomes -500, which underflows to 0 but is handled safely (probability ≈ 0).

The subtraction of max mitigates overflow for standard softmax, but with temperature, you must scale **before** subtracting max. The code does this correctly: `scaled_logits - np.max(scaled_logits)`.

**Key insight:** Temperature can increase overflow risk for very confident models, so use moderate temperatures and always apply the shift for stability.

**Reference:** Slide 4 (How It Works) and Slide 7 (Code Example).

---

## 15. When temperature is used during training (e.g., in a reinforcement learning or distillation setup), are there additional considerations regarding gradient flow or model convergence that might make certain temperature ranges problematic?

**Answer:**  
During **training**, temperature affects the **softness** of probability distributions:
- **High temperature** produces flatter distributions, leading to smaller gradients (since probabilities are more uniform), which can slow convergence or cause instability.
- **Low temperature** creates peaked distributions, leading to large gradients for the correct tokens but potential overfitting or reduced exploration.

In reinforcement learning (e.g., policy gradient methods), temperature can act as an exploration parameter—too low leads to premature convergence, too high leads to noisy learning. In distillation, temperature softens the teacher’s logits to transfer nuanced knowledge, but setting it too high may lose critical information.

**Best practice:** Treat temperature as a **training hyperparameter** only in these special cases; otherwise, keep it fixed at inference and tune during validation if necessary. Monitor gradient magnitudes and reward stability (RL) or distillation loss (Slide 13, Use Cases).

**Reference:** Slide 2 (Definition) and implicit training considerations in Slide 13.