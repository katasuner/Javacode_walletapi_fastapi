from fastapi import FastAPI


app = FastAPI()



if __name__ == "__main__":
    import uvicourn
    uvicourn.run(app, host="127.0.0.0", port="8000")


