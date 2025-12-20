from twelvedata import TDClient
import pandas as pd
import os
import time
from datetime import datetime, timedelta

# ================= KONFIGURASI =================
API_KEY = "e7a04d7c039c42539292a352864bf2fb"  # <--- GANTI INI
TICKERS = ['QQQ', 'NVDA', 'TSLA', 'AAPL', 'AMZN', 'MSFT', 'GOOGL', 'NFLX']
INTERVAL = '1min' 
START_DATE = "2023-01-01" # Coba dari 2023 dulu (Limit free tier biasanya 1-2 tahun)
OUTPUT_FOLDER = "market_data_twelve1min"
# ===============================================

def run_downloader():
    if API_KEY == "MASUKKAN_API_KEY_ANDA_DISINI":
        print("ERROR: Harap masukkan API Key Twelve Data Anda di skrip.")
        return

    if not os.path.exists(OUTPUT_FOLDER):
        os.makedirs(OUTPUT_FOLDER)

    td = TDClient(apikey=API_KEY)
    
    print(f"--- TWELVE DATA DOWNLOADER ---")
    print(f"Interval: {INTERVAL} | Start: {START_DATE}")
    print("NOTE: Script akan berjalan pelan (sleep 15s) untuk mematuhi limit 8 req/menit.\n")

    for ticker in TICKERS:
        print(f"Processing {ticker}...", end=" ", flush=True)
        
        all_dfs = []
        current_start = datetime.strptime(START_DATE, "%Y-%m-%d")
        end_date = datetime.now()
        
        # Loop per 2 bulan (agar aman di bawah limit 5000 baris per request)
        # 1 hari trading ~78 bar (5m). 60 hari ~4680 bar. Pas.
        while current_start < end_date:
            current_end = current_start + timedelta(days=60)
            if current_end > end_date: current_end = end_date
            
            s_str = current_start.strftime("%Y-%m-%d")
            e_str = current_end.strftime("%Y-%m-%d")
            
            try:
                # Construct time series
                ts = td.time_series(
                    symbol=ticker,
                    interval=INTERVAL,
                    start_date=s_str,
                    end_date=e_str,
                    outputsize=5000,
                    timezone="UTC"
                )
                
                # Konversi ke Pandas
                df = ts.as_pandas()
                
                if df is not None and not df.empty:
                    all_dfs.append(df)
                    print(".", end="", flush=True)
                else:
                    print("x", end="", flush=True)

            except Exception as e:
                print(f"!", end="", flush=True)
            
            # Geser tanggal
            current_start = current_end
            
            # --- PENTING: RATE LIMIT ---
            # Free tier max 8 req/min. Kita beri jeda 8 detik per request biar aman.
            time.sleep(8)

        # Gabungkan dan Simpan
        if all_dfs:
            full_df = pd.concat(all_dfs)
            full_df.sort_index(inplace=True)
            # Hapus duplikat baris (overlap tanggal)
            full_df = full_df[~full_df.index.duplicated(keep='first')]
            
            # Format ulang agar mirip yfinance (Index=Datetime, Kolom=Open,High,Low,Close,Volume)
            full_df.index.name = 'Datetime'
            
            # Reset index agar Datetime jadi kolom (untuk CSV)
            full_df.reset_index(inplace=True)
            
            filename = f"{ticker}_1m.csv"
            save_path = os.path.join(OUTPUT_FOLDER, filename)
            full_df.to_csv(save_path, index=False)
            
            print(f" OK! ({len(full_df)} baris)")
            print(f"    Saved to: {filename}")
        else:
            print(" GAGAL/KOSONG.")
            
        print("-" * 30)

if __name__ == "__main__":
    run_downloader()