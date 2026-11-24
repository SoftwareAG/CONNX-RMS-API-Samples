# RMS customer file mapping

This page describes the OpenVMS RMS file behind the samples (`CUSTOMER.DAT`), how CONNX presents it as the relational table `RMS.dbo.customers_rms`, and what that means for keys, IDs, and queries. Use it to reproduce the mapping in your own CONNX Data Dictionary (CDD), or to check that an existing mapping matches what the samples expect.

The details below were read from a working CONNX mapping through ODBC catalog calls (`SQLColumns`, `SQLPrimaryKeys`, `SQLStatistics`), with the CONNX ODBC driver 15.00.

## The RMS file

| Property | Value |
| --- | --- |
| File name | `CUSTOMER.DAT` |
| Organization | Indexed |
| Record format | Fixed length, 111 bytes |
| Fields | 8 fixed-width character fields (see the layout below) |
| Primary key (key 0) | `customerid`, 5 bytes at offset 0, no duplicates |
| Alternate keys | None |

An equivalent empty file can be created on OpenVMS from this FDL. It is derived from the layout above; compare it with `ANALYZE/RMS_FILE/FDL` output for your own file before relying on it.

```text
IDENT   "CONNX RMS customer sample"

FILE
        ORGANIZATION            indexed

RECORD
        CARRIAGE_CONTROL        carriage_return
        FORMAT                  fixed
        SIZE                    111

KEY 0
        CHANGES                 no
        DUPLICATES              no
        NAME                    "CUSTOMERID"
        SEG0_LENGTH             5
        SEG0_POSITION           0
        TYPE                    string
```

```text
$ CREATE/FDL=CUSTOMER.FDL CUSTOMER.DAT
```

## Record layout and relational columns

Each RMS field maps to one `CHAR` column. Offsets are zero-based byte positions within the 111-byte record.

| Offset | Length | RMS field | CONNX column | SQL type | API / model field |
| ---: | ---: | --- | --- | --- | --- |
| 0 | 5 | Customer ID (key 0) | `customerid` | `CHAR(5)` | `customer_id` |
| 5 | 31 | Name | `customername` | `CHAR(31)` | `name` |
| 36 | 22 | Street address | `customeraddress` | `CHAR(22)` | `address` |
| 58 | 14 | City | `customercity` | `CHAR(14)` | `city` |
| 72 | 10 | State / region | `customerstate` | `CHAR(10)` | `state` |
| 82 | 8 | Postal code | `customerzip` | `CHAR(8)` | `zip_code` |
| 90 | 7 | Country | `customercountry` | `CHAR(7)` | `country` |
| 97 | 14 | Phone | `customerphone` | `CHAR(14)` | `phone` |

The API and CLI field names come from `python/src/connx_rms_showcase/models.py`; the Pydantic models enforce the same maximum lengths, so a value that would not fit the RMS field is rejected before it reaches CONNX.

## Keys and indexes

CONNX reports one unique index, `customers_rms_INDEX_0` on `customerid`, and exposes it as the primary key `PK_customers_rms`. This is the RMS primary key (key 0).

- Lookups by `customerid` (`WHERE customerid = ?`) use the RMS key and are fast.
- `ORDER BY customerid` returns records in key order, which is what the list endpoint relies on.
- The file has no alternate keys, so filtering on any other column (name, city, and so on) makes CONNX read the whole file. Add an RMS alternate key, and map it in the CDD, before adding search endpoints on those columns.
- RMS never allows the primary key (key 0) to change, so `customerid` cannot be updated in place. The samples are read-only and never change it.

## `customerid` format

- Exactly 5 characters wide. Shorter values are padded with trailing spaces in the record; the samples trim them on the way out.
- In the demonstration file, every ID is 5 upper-case letters. Lookups are case-sensitive: an upper-case ID is found, the same ID in lower case is not.
- There is no prefix or partial matching on the key through the samples; `get` needs the full ID.
- To find valid IDs, list a few records first:

  ```powershell
  python -m connx_rms_showcase.cli list --limit 5
  ```

## Fixed-width values, blanks, and NULL

- Every RMS field is always physically present in the fixed-length record; RMS itself has no NULL marker.
- CONNX reports all columns as nullable. A field that CONNX returns as NULL is returned by the API and CLI as `null`. All fields in the existing demonstration records are populated.
- A field that is entirely spaces is returned by the API and CLI as an empty string (`""`), not `null`. In the demonstration file this happens for some `customerstate` values.
- Several fields are filled to their full width, so long names and addresses can appear cut off. That is the stored data, not a sample bug.

## SQL dialect

The CONNX mapping is used with strict ANSI-92 SQL. `OFFSET … FETCH` is not available, so the list endpoint reads the ordered result up to `offset + limit` rows and applies the window in Python. Keep page sizes modest on large files; the API caps `limit` at 200.

## Reproducing the mapping in CONNX

1. Make the RMS file (`CUSTOMER.DAT`) reachable from the CONNX server on the OpenVMS host.
2. In the CONNX Data Dictionary Manager, add the file to a CDD, defining the eight fields with the offsets and lengths above (or import the record layout from your existing COBOL, BASIC, or FDL definition).
3. Expose it as `RMS.dbo.customers_rms`, or set `CONNX_RMS_TABLE` to the name you choose.
4. Point a 64-bit ODBC DSN (`CONNX_RMS` by default) at that CDD.
5. Run `python smoketest.py` from `python/`, then check the column list and key with any ODBC catalog tool against the tables above.

Exact CDD import steps depend on your CONNX version; see the CONNX documentation for the RMS adapter.
