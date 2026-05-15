# -*- coding: utf-8 -*-
import pytest

from qwenpaw.agents.tools import file_io


@pytest.mark.asyncio
async def test_read_file_rejects_excel_workbook_raw_read(tmp_path):
    workbook = tmp_path / "classes.xlsx"
    workbook.write_bytes(b"PK\x03\x04 fake xlsx zip bytes")

    response = await file_io.read_file(str(workbook))
    text = response.content[0].get("text", "")

    assert text.startswith("Error:")
    assert "spreadsheet workbook" in text
    assert "bounded spreadsheet reader" in text
    assert "read_file on that CSV" in text


@pytest.mark.asyncio
async def test_read_file_still_reads_csv(tmp_path):
    csv_file = tmp_path / "classes.csv"
    csv_file.write_text("label,value\ncat,1\n", encoding="utf-8")

    response = await file_io.read_file(str(csv_file))
    text = response.content[0].get("text", "")

    assert "label,value" in text
    assert "cat,1" in text
