import marimo

__generated_with = "0.17.7"
app = marimo.App(width="medium")


@app.cell
def _():
    print("hola mundo")
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
