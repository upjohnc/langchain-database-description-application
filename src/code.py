from pprint import pprint

import click
from langchain_community.llms import Ollama
from langchain_community.utilities.sql_database import SQLDatabase
from langchain_core.output_parsers.json import JsonOutputParser
from langchain_core.output_parsers.string import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel


def get_llm():
    llm = Ollama(model="llama3")
    return llm


def get_db():
    db = SQLDatabase.from_uri("sqlite:///Chinook.db")
    return db


def get_table_info(table_name, db):
    table_info = db.get_table_info([table_name])
    return table_info


def get_chain_str(llm):
    prompt = ChatPromptTemplate.from_template(
        """
        system:
        you are a sql analyst

        human:
        Please fill in the following template to provide a table description:
        [Table Name]: _______________________________________________________
        [Column List]:
            • [column1_name] - [column1_description]
            • [column2_name] - [column2_description]
            ...
        [Additional Information]:

        DDL Information: {table_info}
        """
    )
    chain = prompt | llm | StrOutputParser()
    return chain


def get_prompt_json():

    prompt = ChatPromptTemplate.from_template(
        """
        system:
        you are a sql analyst

        human:
        provide a table description anwering with the following json schema:
        {json_schema}

            ...
        [Additional Information]:

        DDL Information: {table_info}
        """
    )
    return prompt


def run_text_response(llm, table_info):
    text_chain = get_chain_str(llm)
    text_response = text_chain.invoke({"table_info": table_info})
    return text_response


def run_json_response(llm, table_info):
    class Column(BaseModel):
        column_name: str
        column_description: str

    class Table(BaseModel):
        table_name: str
        table_description: str
        columns: list[Column]

    parser = JsonOutputParser(pydantic_object=Table)
    chain_json = get_prompt_json() | llm | parser

    json_response = chain_json.invoke(
        {
            "table_info": table_info,
            "json_schema": parser.get_format_instructions(),
        }
    )
    return json_response


@click.command()
@click.option(
    "-r",
    "--response-type",
    type=click.Choice(
        ["json", "text"],
        case_sensitive=False,
    ),
    default="text",
)
@click.option("-t", "--table-name", default="Album")
def main(response_type, table_name):
    llm = get_llm()
    db = get_db()
    table_info = get_table_info(table_name, db)

    if response_type == "json":
        response = run_json_response(llm, table_info)
    else:
        response = run_text_response(llm, table_info)
    pprint(response)


if __name__ == "__main__":
    main()
