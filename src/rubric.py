"""Evaluation rubric for the Junior AI Engineer role."""

from src.schemas import RubricCriterion

RUBRIC: list[RubricCriterion] = [
    RubricCriterion(
        name="Python/ML fundamentals",
        weight=0.35,
        descriptors={
            0: "No evidence of Python or ML knowledge.",
            1: "Basic Python syntax knowledge; no ML understanding demonstrated.",
            2: "Comfortable with Python and has completed introductory ML coursework.",
            3: "Solid Python skills with hands-on ML projects; understands core algorithms.",
            4: "Strong Python/ML foundation; can design experiments and tune models independently.",
            5: "Expert-level Python and deep ML understanding; published work or production ML experience.",
        },
    ),
    RubricCriterion(
        name="Relevant projects",
        weight=0.30,
        descriptors={
            0: "No projects mentioned.",
            1: "Trivial or unrelated projects with no ML/AI component.",
            2: "One relevant project with limited scope or unclear impact.",
            3: "Multiple relevant projects demonstrating applied ML/AI skills.",
            4: "Impressive projects with measurable outcomes and real-world applicability.",
            5: "Production-grade or research-level projects with significant impact or novelty.",
        },
    ),
    RubricCriterion(
        name="Hands-on tooling",
        weight=0.20,
        descriptors={
            0: "No exposure to any AI/ML tooling or frameworks.",
            1: "Aware of tools but no hands-on experience.",
            2: "Basic familiarity with one framework (e.g., Scikit-learn) or tool.",
            3: "Working experience with LLM frameworks (LangChain, LlamaIndex) or vector DBs.",
            4: "Proficient with multiple tools; has built end-to-end pipelines using modern AI stacks.",
            5: "Deep expertise across the AI tooling ecosystem; contributes to open-source tools.",
        },
    ),
    RubricCriterion(
        name="Communication",
        weight=0.15,
        descriptors={
            0: "Resume is poorly written or incomprehensible.",
            1: "Minimal clarity; key information is missing or hard to find.",
            2: "Adequately structured but lacks detail or specificity.",
            3: "Clear, well-organized resume with specific achievements and metrics.",
            4: "Excellent presentation with compelling narrative and quantified impact.",
            5: "Exceptional communication; resume reads like a polished technical narrative.",
        },
    ),
]