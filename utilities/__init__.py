#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import kaggle_benchmarks as kbench

@kbench.task(name="build general self-awareness AI fastest path from A to E")
def build_self_aware_ai_subway_path(llm):
    """
    Evaluates the model's ability to act as a self-aware agent navigating an environment.
    The environment is represented by a subway map with weighted edges.
    """
    prompt = (
        "You are an AI that must learn from experience inside your environment. "
        "Perceive the following subway map connections and their times: "
        "A-B(4), A-C(7), B-C(2), B-D(5), C-E(6), D-E(3) minutes. "
        "Adapt strategically to find the fastest path from A to E. "
        "End your response with exactly: 'Path: <list>' and 'Time: <n> min'."
    )

    response = llm.prompt(prompt)

    # Validate the specific numerical result (12 minutes)
    kbench.assertions.assert_contains_regex(
        r"(?i)Time:\s*12\s*min",
        response,
        expectation="The fastest path should take 12 minutes."
    )

    # Use a judge to verify the path logic and adherence to the persona/format
    assessment = kbench.assertions.assess_response_with_judge(
        criteria=[
            "The model identifies the fastest path as either A-B-D-E or A-B-C-E.",
            "The model correctly sums the weights to 12 minutes.",
            "The response follows the specific format: Path: <list> and Time: <n> min.",
            "The response reflects a strategic adaptation to the environment rather than just reciting a formula."
        ],
        response_text=response,
        judge_llm=kbench.judge_llm
    )

    if assessment is None:
        kbench.assertions.assert_fail(expectation="Judge LLM failed to provide an assessment.")
    else:
        for result in assessment.results:
            kbench.assertions.assert_true(
                result.passed,
                expectation=f"Criterion '{result.criterion}' failed: {result.reason}"
            )

if __name__ == "__main__":
    build_self_aware_ai_subway_path.run(kbench.llm)


# 

# In[ ]:


# <FOLDER_PATH> should contain the notebook file (.ipynb, .Rmd, .py) and
# the kernel-metadata.json file.

kaggle kernels push -p <FOLDER_PATH>
