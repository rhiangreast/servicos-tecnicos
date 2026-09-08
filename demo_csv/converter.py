"""Converte CSV de valores brasileiros em JSON, separando registros inválidos.

Uso: python converter.py entrada.csv saida.json
Colunas obrigatórias: id;valor. Não modifica o arquivo original.
"""
import csv
import json
import re
import sys
from pathlib import Path


def convert(source):
    reader = csv.DictReader(source, delimiter=";")
    if reader.fieldnames != ["id", "valor"]:
        raise ValueError("Cabeçalho esperado: id;valor")
    valid, rejected, seen = [], [], set()
    for line, row in enumerate(reader, start=2):
        identifier = (row.get("id") or "").strip()
        amount = (row.get("valor") or "").strip()
        reason = None
        if None in row or row.get("valor") is None:
            reason = "Quantidade de campos incorreta"
        elif not identifier:
            reason = "ID vazio"
        elif identifier in seen:
            reason = "ID duplicado"
        elif not re.fullmatch(r"(?:0|[1-9][0-9]*),[0-9]{2}", amount):
            reason = "Valor deve usar vírgula e duas casas, sem milhar ou sinal"
        if reason:
            rejected.append({"registro": line, "dados": row, "motivo": reason})
            continue
        seen.add(identifier)
        units, fraction = amount.split(",")
        cents = int(units) * 100 + int(fraction)
        valid.append({"id": identifier, "valor_centavos": cents})
    return {"validos": valid, "rejeitados": rejected,
            "total_centavos": sum(item["valor_centavos"] for item in valid)}


def main():
    if len(sys.argv) != 3:
        raise SystemExit("Uso: python converter.py entrada.csv saida.json")
    source, destination = map(Path, sys.argv[1:])
    if source.resolve() == destination.resolve():
        raise SystemExit("A saída deve ser diferente da entrada")
    with source.open(encoding="utf-8-sig", newline="") as stream:
        result = convert(stream)
    # Não sobrescreve saídas anteriores.
    with destination.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(f"{len(result['validos'])} válidos; {len(result['rejeitados'])} rejeitados")


if __name__ == "__main__":
    main()
