from nox_poetry import Session, session


@session()
def tests(session: Session) -> None:
    args = session.posargs or ["-m", "not slow", "--cov", "--cov-report=xml"]
    session.install(".[all]")
    session.install("pytest")
    session.install("pytest-cov")
    session.run("pytest", *args)


locations = ["forayer", "tests", "noxfile.py"]


@session()
def lint(session: Session) -> None:
    args = session.posargs or locations
    session.install("black", "isort")
    session.run("black", *args)
    session.run("isort", *args)


@session()
def style_checking(session: Session) -> None:
    args = session.posargs or locations
    session.install(
        "pyproject-flake8",
        "flake8-eradicate",
        "flake8-isort",
        "flake8-debugger",
        "flake8-comprehensions",
        "flake8-print",
        "flake8-black",
        "flake8-bugbear",
        "pydocstyle",
    )
    session.run("pflake8", *args)


@session()
def pyroma(session: Session) -> None:
    session.install("poetry-core>=1.0.0")
    session.install("pyroma")
    session.run("pyroma", "--min", "10", ".")


@session()
def type_checking(session: Session) -> None:
    args = session.posargs or locations
    session.install("mypy")
    session.run(
        "mypy",
        "--install-types",
        "--non-interactive",
        "--ignore-missing-imports",
        *args
    )


@session()
def build_doc(session: Session) -> None:
    session.install(".")
    session.install("sphinx")
    session.install("insegel")
    session.cd("docs")
    session.run("make", "clean", external=True)
    session.run("make", "html", external=True)
