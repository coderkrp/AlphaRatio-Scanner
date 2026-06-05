#!/usr/bin/env python
import os
import sys
import zipfile
import xml.etree.ElementTree as ET
import yaml

# Ticker to name mapping for benchmarks
BENCHMARK_NAMES = {
    # Broad Indices
    "^NSEI": "NIFTY50",
    "^CRSLDX": "NIFTY500",
    "^NSMIDCP": "NIFTY_MIDCAP_100",
    "^CNXSC": "NIFTY_SMALLCAP_100",
    "NIFTY_MICROCAP250.NS": "NIFTY_MICROCAP250",
    "NIFTYMIDSML400.NS": "NIFTY_MID_SMALL_400",
    
    # Sectoral Indices
    "^CNXENERGY": "NIFTY_ENERGY",
    "^NSEBANK": "BANKNIFTY",
    "^CNXFIN": "NIFTY_FIN_SERVICES",
    "NIFTY_FIN_SERVICE.NS": "NIFTY_FIN_SERVICES_ETF",
    "^CNXPSE": "NIFTY_PSE",
    "^CNXFMCG": "NIFTY_FMCG",
    "^CNXPHARMA": "NIFTY_PHARMA",
    "^CNXMETAL": "NIFTY_METAL",
    "^CNXREALTY": "NIFTY_REALTY",
    "^CNXIT": "NIFTY_IT",
    "^CNXAUTO": "NIFTY_AUTO",
    "^CNXMEDIA": "NIFTY_MEDIA",
    "NIFTY_CHEMICALS.NS": "NIFTY_CHEMICALS",
    "^CNXCMDT": "NIFTY_COMMODITIES",
    "^CNXCOMMODITIES": "NIFTY_COMMODITIES_INDEX",
    "NIFTY_INDIA_MFG.NS": "NIFTY_INDIA_MFG",
    "MODEFENCE.NS": "NIFTY_DEFENCE",
    "NIFTY_OIL_AND_GAS.NS": "NIFTY_OIL_AND_GAS",
    "^CNXCONSUM": "NIFTY_CONSUMPTION",
    "^CNXINFRA": "NIFTY_INFRASTRUCTURE",
    "^CNXMNC": "NIFTY_MNC",
    "^CNXSERVICE": "NIFTY_SERVICES",
}

def get_benchmark_name(ticker):
    """Returns a standardized name for a benchmark ticker, with dynamic fallback."""
    if ticker in BENCHMARK_NAMES:
        return BENCHMARK_NAMES[ticker]
    # Fallback name generation
    clean_name = ticker.replace("^", "").replace(".NS", "").upper()
    return f"NIFTY_{clean_name}"

def parse_ods(ods_path):
    """Parses ODS file using built-in zipfile and xml libraries to extract rows."""
    if not os.path.exists(ods_path):
        print(f"Error: ODS file not found at {ods_path}")
        sys.exit(1)
        
    print(f"Reading ticker details from ODS: {ods_path}")
    with zipfile.ZipFile(ods_path, 'r') as zip_ref:
        content = zip_ref.read('content.xml')
        
    root = ET.fromstring(content)
    namespaces = {
        'office': 'urn:oasis:names:tc:opendocument:xmlns:office:1.0',
        'table': 'urn:oasis:names:tc:opendocument:xmlns:table:1.0',
        'text': 'urn:oasis:names:tc:opendocument:xmlns:text:1.0',
    }
    
    tables = root.findall('.//table:table', namespaces)
    if not tables:
        print("Error: No tables found in the ODS file.")
        sys.exit(1)
        
    table = tables[0]
    rows = table.findall('.//table:table-row', namespaces)
    
    # Extract headers
    headers = []
    header_cells = rows[0].findall('.//table:table-cell', namespaces)
    for cell in header_cells:
        repeated_cols = cell.get('{urn:oasis:names:tc:opendocument:xmlns:table:1.0}number-columns-repeated')
        count = int(repeated_cols) if repeated_cols else 1
        text_elems = cell.findall('.//text:p', namespaces)
        val = "".join([txt.text for txt in text_elems if txt.text]).strip()
        for _ in range(count):
            headers.append(val)
            
    print(f"Detected columns: {headers}")
    
    # Determine indices for expected columns
    try:
        ticker_idx = headers.index('ticker')
        name_idx = headers.index('name')
        industry_idx = headers.index('Industry')
    except ValueError as e:
        print(f"Error: Missing required column headers in ODS sheet. Required: 'ticker', 'name', 'Industry'. Error: {e}")
        sys.exit(1)
        
    benchmark_idxs = [i for i, h in enumerate(headers) if 'benchmark' in h.lower()]
    max_cols = max(ticker_idx, name_idx, industry_idx, max(benchmark_idxs) if benchmark_idxs else 0) + 1
    
    symbols = []
    
    for row_idx, row in enumerate(rows[1:], start=2):
        cells = row.findall('.//table:table-cell', namespaces)
        row_vals = []
        for cell in cells:
            if len(row_vals) >= max_cols:
                break
            repeated_cols = cell.get('{urn:oasis:names:tc:opendocument:xmlns:table:1.0}number-columns-repeated')
            count = int(repeated_cols) if repeated_cols else 1
            text_elems = cell.findall('.//text:p', namespaces)
            val = "".join([txt.text for txt in text_elems if txt.text]).strip()
            # Stop appending infinitely if LibreOffice repeats blank columns to fill the grid
            for _ in range(min(count, max_cols - len(row_vals))):
                row_vals.append(val)
                
        if len(row_vals) <= ticker_idx or not row_vals[ticker_idx]:
            continue  # Skip empty or header-only lines
            
        # Sanitization
        ticker = row_vals[ticker_idx].strip().upper()
        name = row_vals[name_idx].strip() if len(row_vals) > name_idx else ""
        industry = row_vals[industry_idx].strip() if len(row_vals) > industry_idx else ""
        
        # Enforce ticker formats
        if not ticker.endswith('.NS') and not ticker.startswith('^'):
            print(f"Warning (Row {row_idx}): Ticker '{ticker}' doesn't end with .NS or start with ^. Sanitizing by appending '.NS'.")
            ticker += '.NS'
            
        benchmarks = []
        for idx in benchmark_idxs:
            if idx < len(row_vals):
                bench_ticker = row_vals[idx].strip().upper()
                if bench_ticker:
                    if not bench_ticker.endswith('.NS') and not bench_ticker.startswith('^'):
                        print(f"Warning (Row {row_idx}): Benchmark '{bench_ticker}' doesn't end with .NS or start with ^. Appending '.NS'.")
                        bench_ticker += '.NS'
                    # Deduplicate within symbol benchmarks list
                    if bench_ticker not in benchmarks:
                        benchmarks.append(bench_ticker)
                        
        symbols.append({
            'ticker': ticker,
            'name': name,
            'sector': industry,
            'benchmarks': benchmarks
        })
        
    return symbols

def main():
    # Resolve paths relative to the script directory for robustness
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    
    ods_path = os.path.join(project_root, "ticker details", "ticker details.ods")
    config_path = os.path.join(project_root, "config.yaml")
    config_example_path = os.path.join(project_root, "config.example.yaml")
    
    # 1. Load infrastructure settings from config.yaml or config.example.yaml
    telegram_config = {"token": "YOUR_TELEGRAM_BOT_TOKEN", "chat_id": ["YOUR_CHAT_ID"]}
    database_config = {"url": "sqlite:///./ratio_scanner.db"}
    
    infra_source = None
    if os.path.exists(config_path):
        infra_source = config_path
    elif os.path.exists(config_example_path):
        infra_source = config_example_path
        
    if infra_source:
        print(f"Loading infrastructure configurations from {infra_source}")
        try:
            with open(infra_source, 'r', encoding='utf-8') as f:
                existing_data = yaml.safe_load(f)
                if existing_data:
                    if 'telegram' in existing_data:
                        telegram_config = existing_data['telegram']
                    if 'database' in existing_data:
                        database_config = existing_data['database']
        except Exception as e:
            print(f"Warning: Could not parse existing config file: {e}")

    # 2. Parse symbols from ODS file
    symbols = parse_ods(ods_path)
    print(f"Parsed {len(symbols)} symbols from spreadsheet.")
    
    # Deduplicate symbols if any duplicate tickers exist
    deduped_symbols = {}
    for sym in symbols:
        ticker = sym['ticker']
        if ticker in deduped_symbols:
            print(f"Warning: Duplicate ticker '{ticker}' found in ODS. Merging benchmarks.")
            # Merge benchmarks lists
            existing_bench = set(deduped_symbols[ticker]['benchmarks'])
            existing_bench.update(sym['benchmarks'])
            deduped_symbols[ticker]['benchmarks'] = sorted(list(existing_bench))
        else:
            deduped_symbols[ticker] = sym
            
    sorted_symbols = sorted(deduped_symbols.values(), key=lambda x: x['ticker'])
    
    # 3. Compile unique benchmarks referenced by symbols
    unique_benchmark_tickers = set()
    for sym in sorted_symbols:
        unique_benchmark_tickers.update(sym['benchmarks'])
        
    benchmarks_list = []
    for bench_ticker in sorted(unique_benchmark_tickers):
        benchmarks_list.append({
            'ticker': bench_ticker,
            'name': get_benchmark_name(bench_ticker)
        })
        
    print(f"Compiled {len(benchmarks_list)} unique benchmarks.")
    
    # 4. Construct final yaml data
    config_data = {
        'telegram': telegram_config,
        'database': database_config,
        'benchmarks': benchmarks_list,
        'symbols': sorted_symbols
    }
    
    # 5. Write to config.yaml
    print(f"Writing to {config_path}")
    with open(config_path, 'w', encoding='utf-8') as f:
        f.write("# Generated from ticker details.ods - DO NOT commit credentials to git\n")
        yaml.dump(config_data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
        
    print("Configuration updated successfully.")

if __name__ == "__main__":
    main()
