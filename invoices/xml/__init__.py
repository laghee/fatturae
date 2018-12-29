from __future__ import annotations

from typing import TYPE_CHECKING

from lxml import etree


from .types import XMLDict
from .utils import dict_to_xml

if TYPE_CHECKING:
    from invoices.models import Invoice, Sender, Address


NAMESPACE_MAP = {
    "p": "http://ivaservizi.agenziaentrate.gov.it/docs/xsd/fatture/v1.2",
    "ds": "http://www.w3.org/2000/09/xmldsig#",
    "xsi": "http://www.w3.org/2001/XMLSchema-instance",
}

SCHEMA_LOCATION = (
    "http://ivaservizi.agenziaentrate.gov.it/docs/xsd/fatture/v1.2 "
    "http://www.fatturapa.gov.it/export/fatturazione/sdi/fatturapa/v1.2"
    "/Schema_del_file_xml_FatturaPA_versione_1.2.xsd"
)


def _generate_header(invoice: Invoice) -> XMLDict:
    sender: Sender = invoice.sender
    address: Address = sender.address
    client_address: Address = invoice.recipient_address

    header: XMLDict = {
        "FatturaElettronicaHeader": {
            "DatiTrasmissione": {
                "IdTrasmittente": {
                    "IdPaese": sender.country_code,
                    "IdCodice": sender.code,
                },
                "ProgressivoInvio": invoice.invoice_number,
                "FormatoTrasmissione": invoice.transmission_format,
                "CodiceDestinatario": invoice.recipient_code,
            },
            "CedentePrestatore": {
                "DatiAnagrafici": {
                    "IdFiscaleIVA": {
                        "IdPaese": sender.country_code,
                        "IdCodice": "01234567890",
                    },
                    "Anagrafica": {"Denominazione": sender.company_name},
                    "RegimeFiscale": sender.tax_regime,
                },
                "Sede": {
                    "Indirizzo": address.address,
                    "CAP": address.postcode,
                    "Comune": address.city,
                    "Provincia": address.province,
                    "Nazione": address.country_code,
                },
            },
            "CessionarioCommittente": {
                "DatiAnagrafici": {
                    "CodiceFiscale": invoice.recipient_tax_code,
                    "Anagrafica": {
                        "Nome": invoice.recipient_first_name,
                        "Cognome": invoice.recipient_last_name,
                    },
                },
                "Sede": {
                    "Indirizzo": client_address.address,
                    "CAP": client_address.postcode,
                    "Comune": client_address.city,
                    "Provincia": client_address.province,
                    "Nazione": client_address.country_code,
                },
            },
        }
    }

    return header


def _generate_body(invoice: Invoice) -> XMLDict:
    body: XMLDict = {
        "FatturaElettronicaBody": {
            "DatiGenerali": {
                "DatiGeneraliDocumento": {
                    "TipoDocumento": invoice.invoice_type,
                    "Divisa": invoice.invoice_currency,
                    "Data": invoice.invoice_date.strftime("%Y-%m-%d"),
                    "Numero": invoice.invoice_number,
                    "Causale": invoice.causal,
                },
                "DatiOrdineAcquisto": {
                    "RiferimentoNumeroLinea": 1,
                    "IdDocumento": 66685,
                    "NumItem": 1,
                    "CodiceCUP": "123abc",
                    "CodiceCIG": "456def",
                },
                "DatiContratto": {
                    "RiferimentoNumeroLinea": 1,
                    "IdDocumento": 123,
                    "Data": "2016-09-01",
                    "NumItem": "5",
                    "CodiceCUP": "123abc",
                    "CodiceCIG": "456def",
                },
                "DatiConvenzione": {
                    "RiferimentoNumeroLinea": 1,
                    "IdDocumento": 456,
                    "NumItem": "5",
                    "CodiceCUP": "123abc",
                    "CodiceCIG": "456def",
                },
                "DatiRicezione": {
                    "RiferimentoNumeroLinea": 1,
                    "IdDocumento": 789,
                    "NumItem": "5",
                    "CodiceCUP": "123abc",
                    "CodiceCIG": "456def",
                },
                "DatiTrasporto": {
                    "DatiAnagraficiVettore": {
                        "IdFiscaleIVA": {
                            "IdPaese": "IT",
                            "IdCodice": "24681012141",
                        },
                        "Anagrafica": {"Denominazione": "Trasporto spa"},
                    },
                    "DataOraConsegna": "2017-01-10T16:46:12.000+02:00",
                },
            },
            "DatiBeniServizi": {
                "DettaglioLinee": {
                    "NumeroLinea": 1,
                    "Descrizione": "DESCRIZIONE DELLA FORNITURA",
                    "Quantita": "5.00",
                    "PrezzoUnitario": "1.00",
                    "PrezzoTotale": "5.00",
                    "AliquotaIVA": "22.00",
                },
                "DatiRiepilogo": {
                    "AliquotaIVA": "22.00",
                    "ImponibileImporto": "5.00",
                    "Imposta": "1.10",
                    "EsigibilitaIVA": "I",
                },
            },
            "DatiPagamento": {
                "CondizioniPagamento": "TP01",
                "DettaglioPagamento": {
                    "ModalitaPagamento": "MP01",
                    "DataScadenzaPagamento": "2017-02-18",
                    "ImportoPagamento": "6.10",
                },
            },
        }
    }

    return body


def invoice_to_xml(invoice: Invoice) -> etree._Element:
    root_tag = "{%s}FatturaElettronica" % NAMESPACE_MAP["p"]
    schema_location_key = "{%s}schemaLocation" % NAMESPACE_MAP["xsi"]

    root = etree.Element(
        root_tag,
        attrib={schema_location_key: SCHEMA_LOCATION},
        nsmap=NAMESPACE_MAP,
        versione="FPR12",
    )

    header = _generate_header(invoice)
    body = _generate_body(invoice)

    tags = [*dict_to_xml(header), *dict_to_xml(body)]

    for tag in tags:
        root.append(tag)

    return root
