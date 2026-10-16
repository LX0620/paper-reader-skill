# Algorithms, ML and computational experiments

Identify inputs, outputs, learning/optimization objective, full pipeline, information available at each stage, baselines, and the proposed component. Explain the mechanism connecting the component to the intended benefit. Separate model architecture, optimization procedure, and evaluation design.

Inspect train/validation/test separation, temporal ordering, product/customer/site grouping, data preprocessing, hyperparameter selection, and any access to future/test labels. Evaluate whether baselines receive comparable data, tuning, computational budget, and decision constraints.

Read the actual table/figure, not only its caption. Record dataset/sample size, units, metric definition, seeds/repetitions, variability, and significance procedure when supplied. Distinguish statistical from practical importance. Use ablations to assess which component matters; inspect whether the design isolates that component.

For operations applications, ask whether improvements reach the decision objective: feasible ordering/resource allocation, cost, profit, service, or risk. Better prediction or ranking is not automatically a demonstrated improvement in those outcomes.

Inspect reproducibility evidence: pseudocode, parameter values, data access, implementation details, runtime, hardware, and stopping conditions. Missing implementation detail limits reproducibility but does not automatically invalidate the theoretical idea. Do not claim to have reproduced a result without actually running the authorized code/data and recording differences from the paper's setup.
