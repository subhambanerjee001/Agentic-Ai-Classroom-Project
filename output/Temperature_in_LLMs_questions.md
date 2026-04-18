# Student Questions: Temperature in LLMs

## Clarification Questions

- If temperature is applied to logits before softmax, how does scaling by a value less than 1.0 make the distribution sharper? Could you walk through the math to show why dividing by a small temperature increases the exponent’s magnitude and concentrates probability mass?  
- When we say temperature “controls randomness,” is this randomness solely about token probability distributions, or does it also interact with the deterministic argmax decoding in any way?  
- The formula divides each logit by temperature before subtracting the max for numerical stability. Does the subtraction of max happen before or after scaling by temperature, and does the order affect the final probabilities?  
- In practice, how does temperature interact with model confidence? If the model already assigns a very high probability to a single token, will increasing temperature still meaningfully change the sampling outcome?  
- The slides mention that small temperature changes can significantly alter generated text. Is this sensitivity consistent across different layers or heads in the model, or does it vary depending on which part of the network the temperature is applied to?  

## Application Questions

- For a customer support chatbot that needs to balance factual correctness with engaging responses, what concrete temperature adjustment strategy would you recommend for open-ended versus closed-ended user queries?  
- If you are generating long-form creative content with a high temperature but notice coherence drops, could you dynamically adjust temperature mid-generation (e.g., lower for critical sentences, higher for brainstorming phrases), and how would you decide the switching criteria?  
- When fine-tuning an LLM for a domain-specific task like medical advice, should temperature be treated as a hyperparameter tuned during validation, or is it more effective to keep it fixed at a low value and adjust it only at inference time?  
- In a retrieval-augmented generation setup, how should temperature be set when combining retrieved passages with generated text to ensure consistency between the retrieved evidence and the model’s creative elaboration?  
- Could you design a simple experiment to demonstrate the effect of temperature on output diversity for a given prompt, including metrics you would use to quantify diversity versus coherence?  

## Edge Case Questions

- What happens if temperature is set to exactly 1.0 in the provided code—is this equivalent to leaving the logits unscaled, or does the subtraction of max in the exponent slightly alter the behavior compared to a “no temperature” baseline?  
- If temperature is set to a very high value (e.g., 10.0), causing all logits to become nearly equal, will sampling still be meaningful, and does this scenario expose any numerical issues in the softmax computation?  
- In top‑k or nucleus sampling, can an extremely low temperature cause the probability mass to collapse onto tokens that may be excluded by the filtering steps, leading to empty or invalid candidate sets?  
- If logits contain very large positive or negative values (e.g., due to extreme model confidence), does temperature scaling interact with floating-point underflow/overflow risks differently than in the standard softmax implementation?  
- When temperature is used during training (e.g., in a reinforcement learning or distillation setup) versus inference, are there additional considerations regarding gradient flow or model convergence that might make certain temperature ranges problematic?