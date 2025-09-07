from typing import Union
from fastapi import FastAPI, Response
from repository.dbConfig import DBConfig
from repository.db import DB

from controller.genome import GenomeController
from service.genome import GenomeService
from repository.genome import GenomeRepository

from controller.biosample import BiosampleController
from service.biosample import BiosampleService
from repository.biosample import BiosampleRepository

app = FastAPI()

db = DB(DBConfig())
genomeController = GenomeController(GenomeService(GenomeRepository(db)))
biosampleController = BiosampleController(BiosampleService(BiosampleRepository(db)))

@app.get("/genomes/")
def getGenomesList(response: Response, next: str = None, previous: str = None):
    response.headers["Content-Type"] = "application/json"
    response.headers["Access-Control-Allow-Origin"] = "http://localhost:3000"
    return genomeController.getGenomesList(next, previous)

@app.get("/genomes/{genomeId}")
def getGenome(response: Response, genomeId: str):
    response.headers["Content-Type"] = "application/json"
    response.headers["Access-Control-Allow-Origin"] = "http://localhost:3000"
    return genomeController.getGenome(genomeId)

@app.get("/biosamples/")
def getBiosamplesList(response: Response, next: str = None, previous: str = None):
    response.headers["Content-Type"] = "application/json"
    response.headers["Access-Control-Allow-Origin"] = "http://localhost:3000"
    return biosampleController.getBiosamplesList(next, previous)

@app.get("/biosamples/{biosamplesId}")
def getBiosample(response: Response, biosamplesId: str):
    response.headers["Content-Type"] = "application/json"
    response.headers["Access-Control-Allow-Origin"] = "http://localhost:3000"
    return biosampleController.getBiosample(biosamplesId)

