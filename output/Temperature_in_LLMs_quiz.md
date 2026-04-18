# Quiz: Temperature in LLMs

# Quiz: Temperature in LLMs

## Multiple Choice Questions

**1. What does temperature primarily control in LLM output generation?**  
a) The length of the generated text  
b) The randomness and diversity of token selection  
c) The model's training speed  
d) The number of parameters in the model  

**Answer: b**  
**Explanation:** Temperature is a hyperparameter that scales logits before softmax, directly controlling the randomness and diversity of token probabilities during decoding (Slide 2, 4). Lower values make outputs more deterministic, while higher values increase variability.

---

**2. When using a low temperature (e.g., 0.2), which of the following is most likely?**  
a) Increased creative and varied responses  
b) Higher risk of incoherent outputs  
c) More repetitive and focused responses  
d) Reduced accuracy in factual tasks  

**Answer: c**  
**Explanation:** Low temperature reduces randomness, making the model more focused and deterministic, which often results in repetitive but coherent outputs (Slide 6, 9). This is suitable for factual tasks requiring precision.

---

**3. In the provided code example, what happens to the logits before applying softmax?**  
a) They are multiplied by temperature  
b) They are divided by temperature  
c) They are exponentiated directly  
d) They are normalized to sum to 1  

**Answer: b**  
**Explanation:** The code divides logits by temperature (`scaled_logits = np.array(logits) / temperature`) before converting to probabilities via softmax (Slide 7, 10). This scaling adjusts the probability distribution's sharpness.

---

**4. Which scenario best matches the use of high temperature (e.g., 1.2)?**  
a) Answering factual quiz questions  
b) Generating technical documentation  
c) Creative story writing  
d) Legal contract analysis  

**Answer: c**  
**Explanation:** High temperature introduces variability and originality, making it ideal for creative tasks like story writing (Slide 11, 13). It is discouraged for factual work due to increased incoherence risk.

---

**5. What is a common mistake when using temperature with other sampling methods?**  
a) Using temperature only with top‑p sampling  
b) Ignoring interaction with top‑k or nucleus sampling  
c) Setting temperature to exactly 1.0  
d) Applying temperature before computing logits  

**Answer: b**  
**Explanation:** Temperature should be combined thoughtfully with nucleus or top‑k sampling to balance diversity and coherence. Ignoring this interaction can lead to suboptimal outputs (Slide 14).

---

## Short Answer Questions

**1. Explain how temperature affects the softmax probability distribution.**  
**Answer:**  
Temperature scales the logits before softmax conversion. A low temperature makes the distribution sharper (peaked probabilities), favoring high-probability tokens and reducing randomness. A high temperature flattens the distribution, making low-probability tokens more likely and increasing output diversity (Slides 3, 4, 7).

---

**2. Why might adaptive temperature be beneficial in dialog systems?**  
**Answer:**  
Adaptive temperature balances coherence and engagement in dialog systems. Lower temperature ensures factual consistency and stability, while higher temperature introduces variability to keep conversations interesting and natural (Slide 11, 13).

---

**3. Describe a practical strategy for tuning temperature in a real-world application.**  
**Answer:**  
Start with a moderate temperature (e.g., 0.7) and adjust based on task requirements: lower for factual accuracy (e.g., QA), higher for creative tasks (e.g., writing). Monitor output quality and coherence, and avoid extreme values to prevent repetition or incoherence (Slides 9, 12, 14).