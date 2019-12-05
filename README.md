# BDT based Lambda selection in Belle
MVA based particle selection offers better performance compared
with traditional cut-based selection. In this work, we use FastBDT,
an implmentation of gradient boosting algorithm within the BASF2
software framework, to optimize `Lambda` selection. 

The model is trained on Belle generic MC reconstructed using B2BII.
The signal and background ratio is made to be 1:1 to give a nicer
classifier output.

The `goodLambda` flag is the baseline. We aim to do better.


## How to create a balanced training set
The ratio of the number of of matched candidates to unmatched
is about 1:100. Therefore, to create a balanced training 
set with 50% signal and 50% background, 99% of the unmatched 
candidates need to be discarded. This is done by the cut 
`random < 0.01` for each unmatched candidate.
