# DS-PT2: The Application of Artificial Intelligence to Reduce the time to re--develop of on-market Drugs

## Description

###
"The reformulation of on market drugs is an often used strategy in the lifecycle management of pharmaceutical products. Reformulation allows for the targeting of broader clinical indications. It can also protect market share following the loss of regulatory exclusivity or intellectual property rights. The time required to re-formulate drugs can be critical in protecting the ongoing investment required to develop and market a drug product.

The CAS formulus database contains extensive formulation data which can be accessed to aid in formulation and process development. However mined data can be extensive requiring more refined targeted searching to extract critical information which can eventually aid to determine target formulations.

Furthermore, literature searches can provide formulation data that can significantly shorten development timelines. These searches however can generate large volumes of data from which extraction of specific formulation and process data can be a slow, manual process.

It is envisaged that this collaboration will investigate the leveraging of Artificial Intelligence in a commercially viable way. A review of existing Artificial Intelligence systems could be conducted to determine whether any platforms exist or could be extended, to allow for extraction of available data leading to faster development times in the re-formulation of on market drugs."

## Architecture
![Architecture](https://github.com/jackylove5/DS-PT2/blob/main/doc/pipeline.png?raw=true)

## Requirement
- Requests and BeautifulSoup
- FuzzyWuzzy
- Pdf2image
- [PaddleOCR 2.1.1](https://github.com/PaddlePaddle/PaddleOCR/blob/release/2.2/ppstructure/README.md)
- [TPOT](https://github.com/EpistasisLab/tpot)

## Usage
```bash
python main.py
```
