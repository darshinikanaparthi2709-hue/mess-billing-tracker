import http.server
import socketserver
import json
import sqlite3
import re
import os
from datetime import datetime

PORT = 8000
DB_FILE = "messdb.db"

MYSQL_CONFIG = {
    "host": "127.0.0.1",
    "port": 3306,
    "user": "root",
    "password": "",
    "database": "messdb"
}

USE_MYSQL = False

DEFAULT_COMPANIES = [
    {
        "id": 1,
        "name": "Everest Infra Ventures India Pvt. Ltd.",
        "since": "Jan 2025",
        "filename": "everest_infra_ventures_india_pvt__ltd.sql",
        "table_name": "everest infra ventures india pvt. ltd"
    },
    {
        "id": 2,
        "name": "MediJourn Solutions Pvt. Ltd.",
        "since": "Mar 2025",
        "filename": "medijourn_solutions_pvt__ltd_.sql",
        "table_name": "medijourn solutions pvt. ltd."
    },
    {
        "id": 3,
        "name": "Wadi Surgicals Pvt. Ltd.",
        "since": "Jun 2024",
        "filename": "wadi_surgicals_pvt__ltd_.sql",
        "table_name": "wadi surgicals pvt. ltd."
    },
    {
        "id": 4,
        "name": "Fristor Foods Pvt. Ltd.",
        "since": "Nov 2024",
        "filename": "fristor_foods_pvt__ltd_.sql",
        "table_name": "fristor foods pvt. ltd."
    }
]

DEFAULT_CONFIG = {
    "messName": "Sri Karthikeya Deluxe Mess",
    "location": "Somajiguda, Hyderabad — 500082",
    "defaultMeal": "Egg Meals",
    "prices": {
        "egg": 120,
        "veg": 120,
        "chicken": 160,
        "mutton": 275
    }
}

def check_mysql_connection():
    global USE_MYSQL
    try:
        import pymysql
        # Try connecting to MySQL server to ensure it is running and create DB
        conn = pymysql.connect(
            host=MYSQL_CONFIG["host"],
            port=MYSQL_CONFIG["port"],
            user=MYSQL_CONFIG["user"],
            password=MYSQL_CONFIG["password"]
        )
        cursor = conn.cursor()
        cursor.execute("CREATE DATABASE IF NOT EXISTS `messdb` CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;")
        conn.commit()
        conn.close()
        
        # Test connection to the specific database
        conn = pymysql.connect(
            host=MYSQL_CONFIG["host"],
            port=MYSQL_CONFIG["port"],
            user=MYSQL_CONFIG["user"],
            password=MYSQL_CONFIG["password"],
            database=MYSQL_CONFIG["database"]
        )
        conn.close()
        USE_MYSQL = True
        print("Connected successfully to local MySQL server ('messdb' database active).")
        return True
    except Exception as e:
        print(f"MySQL connection failed: {e}. Falling back to SQLite database.")
        USE_MYSQL = False
        return False

def init_db():
    if USE_MYSQL:
        init_db_mysql()
    else:
        init_db_sqlite()

def init_db_sqlite():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # 1. Config Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS config (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL
    )
    """)
    cursor.execute("SELECT count(*) FROM config")
    if cursor.fetchone()[0] == 0:
        for k, v in DEFAULT_CONFIG.items():
            cursor.execute("INSERT INTO config (key, value) VALUES (?, ?)", (k, json.dumps(v)))
            
    # 2. Companies Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS companies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        since TEXT NOT NULL,
        filename TEXT NOT NULL,
        table_name TEXT NOT NULL
    )
    """)
    cursor.execute("SELECT count(*) FROM companies")
    if cursor.fetchone()[0] == 0:
        for c in DEFAULT_COMPANIES:
            cursor.execute("""
            INSERT INTO companies (id, name, since, filename, table_name)
            VALUES (?, ?, ?, ?, ?)
            """, (c["id"], c["name"], c["since"], c["filename"], c["table_name"]))
            
    # 3. Unified Entries Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS entries (
        date TEXT NOT NULL,
        company_id INTEGER NOT NULL,
        egg INTEGER NOT NULL DEFAULT 0,
        veg INTEGER NOT NULL DEFAULT 0,
        chicken INTEGER NOT NULL DEFAULT 0,
        mutton INTEGER NOT NULL DEFAULT 0,
        PRIMARY KEY (date, company_id)
    )
    """)
    
    conn.commit()
    conn.close()

def init_db_mysql():
    import pymysql
    conn = pymysql.connect(
        host=MYSQL_CONFIG["host"],
        port=MYSQL_CONFIG["port"],
        user=MYSQL_CONFIG["user"],
        password=MYSQL_CONFIG["password"],
        database=MYSQL_CONFIG["database"]
    )
    cursor = conn.cursor()
    
    # 1. Config Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS config (
        `key` VARCHAR(255) NOT NULL,
        `value` TEXT NOT NULL,
        PRIMARY KEY (`key`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
    """)
    cursor.execute("SELECT count(*) FROM config")
    if cursor.fetchone()[0] == 0:
        for k, v in DEFAULT_CONFIG.items():
            cursor.execute("INSERT INTO config (`key`, `value`) VALUES (%s, %s)", (k, json.dumps(v)))
            
    # 2. Companies Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS companies (
        `id` INT NOT NULL AUTO_INCREMENT,
        `name` VARCHAR(255) NOT NULL,
        `since` VARCHAR(50) NOT NULL,
        `filename` VARCHAR(255) NOT NULL,
        `table_name` VARCHAR(255) NOT NULL,
        PRIMARY KEY (`id`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
    """)
    cursor.execute("SELECT count(*) FROM companies")
    if cursor.fetchone()[0] == 0:
        for c in DEFAULT_COMPANIES:
            cursor.execute("""
            INSERT INTO companies (`id`, `name`, `since`, `filename`, `table_name`)
            VALUES (%s, %s, %s, %s, %s)
            """, (c["id"], c["name"], c["since"], c["filename"], c["table_name"]))
            
    # 3. Unified Entries Table in MySQL
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS entries (
        `date` varchar(10) NOT NULL,
        `company_id` int(11) NOT NULL,
        `egg` int(11) NOT NULL DEFAULT 0,
        `veg` int(11) NOT NULL DEFAULT 0,
        `chicken` int(11) NOT NULL DEFAULT 0,
        `mutton` int(11) NOT NULL DEFAULT 0,
        PRIMARY KEY (`date`, `company_id`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
    """)

    # 4. Fetch companies and auto-migrate historical daily logs to central entries
    cursor.execute("SELECT id, table_name FROM companies")
    companies_rows = cursor.fetchall()
    
    for comp in companies_rows:
        comp_id = comp[0]
        t_name = comp[1]
        
        # Check if table exists
        cursor.execute(f"SHOW TABLES LIKE '{t_name}'")
        t_exists = cursor.fetchone()
        
        if t_exists:
            # Check if old table has DATE column to import from
            try:
                cursor.execute(f"SHOW COLUMNS FROM `{t_name}` LIKE 'DATE'")
                column_date_exists = cursor.fetchone()
                if column_date_exists:
                    print(f"Migrating records from table '{t_name}' to central entries log...")
                    cursor.execute(f"SELECT `DATE`, `EGG`, `VEG`, `CHICKEN`, `MUTTON` FROM `{t_name}`")
                    old_records = cursor.fetchall()
                    for r in old_records:
                        cursor.execute("""
                        INSERT INTO entries (`date`, `company_id`, `egg`, `veg`, `chicken`, `mutton`)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE
                            `egg` = VALUES(`egg`),
                            `veg` = VALUES(`veg`),
                            `chicken` = VALUES(`chicken`),
                            `mutton` = VALUES(`mutton`)
                        """, (r[0], comp_id, r[1], r[2], r[3], r[4]))
            except Exception as migrate_err:
                print(f"Note migrating table '{t_name}': {migrate_err}")

    # 5. Build/Update individual company tables with Invoice SNO structure
    for comp in companies_rows:
        comp_id = comp[0]
        t_name = comp[1]
        
        cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS `{t_name}` (
          `SNO` int(11) NOT NULL AUTO_INCREMENT,
          `MEAL_TYPE` varchar(50) NOT NULL,
          `DESCRIPTION` varchar(255) NOT NULL,
          `NO_OF_PERSONS` int(11) NOT NULL,
          `DAYS` int(11) NOT NULL,
          `TOTAL_MEALS` int(11) NOT NULL,
          `RATE` decimal(10,2) NOT NULL,
          `AMOUNT` decimal(10,2) NOT NULL,
          `BILL_MONTH` varchar(50) NOT NULL,
          PRIMARY KEY (`SNO`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
        """)

    conn.commit()
    conn.close()

def make_safe_filename(company_name):
    s = company_name.lower()
    s = re.sub(r'[^a-z0-9]+', '_', s)
    s = s.strip('_')
    s = s.replace("pvt_ltd", "pvt__ltd")
    if not s.endswith("_"):
        s += "_"
    return f"{s}.sql"

def get_config_prices():
    prices = {"egg": 120, "veg": 120, "chicken": 160, "mutton": 275}
    try:
        if USE_MYSQL:
            import pymysql
            conn = pymysql.connect(
                host=MYSQL_CONFIG["host"],
                port=MYSQL_CONFIG["port"],
                user=MYSQL_CONFIG["user"],
                password=MYSQL_CONFIG["password"],
                database=MYSQL_CONFIG["database"]
            )
            cursor = conn.cursor()
            cursor.execute("SELECT `value` FROM config WHERE `key` = 'prices'")
            row = cursor.fetchone()
            if row:
                prices.update(json.loads(row[0]))
            conn.close()
        else:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM config WHERE key = 'prices'")
            row = cursor.fetchone()
            if row:
                prices.update(json.loads(row[0]))
            conn.close()
    except Exception as e:
        print(f"Error loading config prices: {e}")
    return prices

def get_invoice_rows(company_id):
    raw_rows = []
    try:
        if USE_MYSQL:
            import pymysql
            conn = pymysql.connect(
                host=MYSQL_CONFIG["host"],
                port=MYSQL_CONFIG["port"],
                user=MYSQL_CONFIG["user"],
                password=MYSQL_CONFIG["password"],
                database=MYSQL_CONFIG["database"]
            )
            cursor = conn.cursor()
            cursor.execute("SELECT `date`, `egg`, `veg`, `chicken`, `mutton` FROM `entries` WHERE `company_id` = %s ORDER BY `date` ASC", (company_id,))
            raw_rows = cursor.fetchall()
            conn.close()
        else:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute("SELECT date, egg, veg, chicken, mutton FROM entries WHERE company_id = ? ORDER BY date ASC", (company_id,))
            raw_rows = cursor.fetchall()
            conn.close()
    except Exception as e:
        print(f"Error fetching raw entries for aggregation: {e}")
        return []

    prices = get_config_prices()
    
    months_data = {}
    for r in raw_rows:
        date_str = r[0]
        match = re.match(r"(\d{4})-(\d{2})-(\d{2})", date_str)
        if not match:
            continue
        year, month, day = match.groups()
        ym_key = f"{year}-{month}"
        if ym_key not in months_data:
            months_data[ym_key] = []
        months_data[ym_key].append({
            "day": int(day),
            "egg": r[1],
            "veg": r[2],
            "chicken": r[3],
            "mutton": r[4]
        })

    ym_keys_sorted = sorted(months_data.keys())
    invoice_rows = []
    sno = 1
    months_names = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]

    for ym in ym_keys_sorted:
        year_str, month_str = ym.split("-")
        month_idx = int(month_str) - 1
        bill_month = f"{months_names[month_idx]} {year_str}"
        
        meal_types = [
            {"key": "veg", "label": "VEG MEALS", "rate": prices.get("veg", 120)},
            {"key": "egg", "label": "EGG MEALS", "rate": prices.get("egg", 120)},
            {"key": "chicken", "label": "CHICKEN MEALS", "rate": prices.get("chicken", 160)},
            {"key": "mutton", "label": "MUTTON", "rate": prices.get("mutton", 275)}
        ]
        
        day_entries = months_data[ym]
        
        for mt in meal_types:
            key = mt["key"]
            label = mt["label"]
            rate = mt["rate"]
            
            active = [de for de in day_entries if de[key] > 0]
            if not active:
                continue
                
            groups = {}
            for de in active:
                count = de[key]
                if count not in groups:
                    groups[count] = []
                groups[count].append(de["day"])
                
            for count in sorted(groups.keys(), reverse=True):
                days_list = sorted(groups[count])
                desc = ",".join(str(d) for d in days_list)
                days_count = len(days_list)
                total_meals = count * days_count
                amount = total_meals * rate
                
                invoice_rows.append({
                    "sno": sno,
                    "meal_type": label,
                    "description": desc,
                    "no_of_persons": count,
                    "days": days_count,
                    "total_meals": total_meals,
                    "rate": float(rate),
                    "amount": float(amount),
                    "bill_month": bill_month
                })
                sno += 1
                
    return invoice_rows

def regenerate_sql_file(filename, table_name, company_id):
    invoice_rows = get_invoice_rows(company_id)
    
    # If MySQL is enabled, synchronize the physical company tables format
    if USE_MYSQL:
        try:
            import pymysql
            conn = pymysql.connect(
                host=MYSQL_CONFIG["host"],
                port=MYSQL_CONFIG["port"],
                user=MYSQL_CONFIG["user"],
                password=MYSQL_CONFIG["password"],
                database=MYSQL_CONFIG["database"]
            )
            cursor = conn.cursor()
            # Drop old daily structure table if it doesn't match new layout (recreate it)
            cursor.execute(f"DROP TABLE IF EXISTS `{table_name}`")
            cursor.execute(f"""
            CREATE TABLE `{table_name}` (
              `SNO` int(11) NOT NULL AUTO_INCREMENT,
              `MEAL_TYPE` varchar(50) NOT NULL,
              `DESCRIPTION` varchar(255) NOT NULL,
              `NO_OF_PERSONS` int(11) NOT NULL,
              `DAYS` int(11) NOT NULL,
              `TOTAL_MEALS` int(11) NOT NULL,
              `RATE` decimal(10,2) NOT NULL,
              `AMOUNT` decimal(10,2) NOT NULL,
              `BILL_MONTH` varchar(50) NOT NULL,
              PRIMARY KEY (`SNO`)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
            """)
            
            for r in invoice_rows:
                cursor.execute(f"""
                INSERT INTO `{table_name}` (`SNO`, `MEAL_TYPE`, `DESCRIPTION`, `NO_OF_PERSONS`, `DAYS`, `TOTAL_MEALS`, `RATE`, `AMOUNT`, `BILL_MONTH`)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (r["sno"], r["meal_type"], r["description"], r["no_of_persons"], r["days"], r["total_meals"], r["rate"], r["amount"], r["bill_month"]))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Error synchronizing MySQL company table `{table_name}`: {e}")
            
    gen_time = datetime.now().strftime("%B %d, %Y at %I:%M %p")
    
    content = f"""-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Generation Time: {gen_time}
-- Server version: 10.4.32-MariaDB
-- PHP Version: 8.2.12

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `messdb`
--

-- --------------------------------------------------------

--
-- Table structure for table `{table_name}`
--

CREATE TABLE `{table_name}` (
  `SNO` int(11) NOT NULL AUTO_INCREMENT,
  `MEAL_TYPE` varchar(50) NOT NULL,
  `DESCRIPTION` varchar(255) NOT NULL,
  `NO_OF_PERSONS` int(11) NOT NULL,
  `DAYS` int(11) NOT NULL,
  `TOTAL_MEALS` int(11) NOT NULL,
  `RATE` decimal(10,2) NOT NULL,
  `AMOUNT` decimal(10,2) NOT NULL,
  `BILL_MONTH` varchar(50) NOT NULL,
  PRIMARY KEY (`SNO`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
"""

    if invoice_rows:
        content += f"""
--
-- Dumping data for table `{table_name}`
--

INSERT INTO `{table_name}` (`SNO`, `MEAL_TYPE`, `DESCRIPTION`, `NO_OF_PERSONS`, `DAYS`, `TOTAL_MEALS`, `RATE`, `AMOUNT`, `BILL_MONTH`) VALUES
"""
        val_list = []
        for r in invoice_rows:
            val_list.append(f"({r['sno']}, '{r['meal_type']}', '{r['description']}', {r['no_of_persons']}, {r['days']}, {r['total_meals']}, {r['rate']:.2f}, {r['amount']:.2f}, '{r['bill_month']}')")
        content += ",\n".join(val_list) + ";\n"
        
    content += """COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
"""
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)

class APIRequestHandler(http.server.BaseHTTPRequestHandler):
    def _set_headers(self, status=200, content_type='application/json'):
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_OPTIONS(self):
        self._set_headers(200)

    def do_GET(self):
        if self.path.startswith('/api/'):
            if self.path == '/api/data':
                config_data = {}
                companies_list = []
                entries_data = {}
                
                if USE_MYSQL:
                    import pymysql
                    conn = pymysql.connect(
                        host=MYSQL_CONFIG["host"],
                        port=MYSQL_CONFIG["port"],
                        user=MYSQL_CONFIG["user"],
                        password=MYSQL_CONFIG["password"],
                        database=MYSQL_CONFIG["database"]
                    )
                    cursor = conn.cursor()
                    
                    # 1. Fetch Config
                    cursor.execute("SELECT `key`, `value` FROM config")
                    for row in cursor.fetchall():
                        config_data[row[0]] = json.loads(row[1])
                        
                    # 2. Fetch Companies
                    cursor.execute("SELECT `id`, `name`, `since`, `filename`, `table_name` FROM companies")
                    for row in cursor.fetchall():
                        companies_list.append({
                            "id": row[0],
                            "name": row[1],
                            "since": row[2],
                            "filename": row[3],
                            "table_name": row[4]
                        })
                        
                    # 3. Fetch Entries from unified table
                    try:
                        cursor.execute("SELECT `date`, `company_id`, `egg`, `veg`, `chicken`, `mutton` FROM `entries`")
                        for row in cursor.fetchall():
                            key = f"{row[0]}_{row[1]}"
                            entries_data[key] = {
                                "egg": row[2],
                                "veg": row[3],
                                "chicken": row[4],
                                "mutton": row[5]
                            }
                    except Exception as entries_err:
                        print(f"Error querying entries table in MySQL: {entries_err}")
                            
                    conn.close()
                else:
                    conn = sqlite3.connect(DB_FILE)
                    cursor = conn.cursor()
                    
                    # 1. Fetch Config
                    cursor.execute("SELECT key, value FROM config")
                    for row in cursor.fetchall():
                        config_data[row[0]] = json.loads(row[1])
                        
                    # 2. Fetch Companies
                    cursor.execute("SELECT id, name, since, filename, table_name FROM companies")
                    for row in cursor.fetchall():
                        companies_list.append({
                            "id": row[0],
                            "name": row[1],
                            "since": row[2],
                            "filename": row[3],
                            "table_name": row[4]
                        })
                        
                    # 3. Fetch Entries from unified table
                    cursor.execute("SELECT date, company_id, egg, veg, chicken, mutton FROM entries")
                    for row in cursor.fetchall():
                        key = f"{row[0]}_{row[1]}"
                        entries_data[key] = {
                            "egg": row[2],
                            "veg": row[3],
                            "chicken": row[4],
                            "mutton": row[5]
                        }
                    conn.close()
                
                response = {
                    "config": config_data,
                    "companies": companies_list,
                    "entries": entries_data
                }
                
                self._set_headers(200)
                self.wfile.write(json.dumps(response).encode('utf-8'))
            else:
                self._set_headers(404)
                self.wfile.write(json.dumps({"error": "Endpoint not found"}).encode('utf-8'))
        else:
            # Serve static files
            path = self.path.split('?')[0].split('#')[0]
            if path == '/':
                path = '/index.html'
            
            filepath = os.path.join(os.getcwd(), path.lstrip('/'))
            
            if not os.path.abspath(filepath).startswith(os.getcwd()):
                self.send_response(403)
                self.end_headers()
                self.wfile.write(b"Forbidden")
                return
                
            if os.path.exists(filepath) and os.path.isfile(filepath):
                mime = 'text/html'
                if filepath.endswith('.css'):
                    mime = 'text/css'
                elif filepath.endswith('.js'):
                    mime = 'application/javascript'
                elif filepath.endswith('.png'):
                    mime = 'image/png'
                elif filepath.endswith('.jpg') or filepath.endswith('.jpeg'):
                    mime = 'image/jpeg'
                elif filepath.endswith('.svg'):
                    mime = 'image/svg+xml'
                elif filepath.endswith('.ico'):
                    mime = 'image/x-icon'
                
                self._set_headers(200, content_type=mime)
                with open(filepath, 'rb') as f:
                    self.wfile.write(f.read())
            else:
                self._set_headers(404, content_type='text/plain')
                self.wfile.write(b"File not found")

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        data = json.loads(post_data.decode('utf-8'))
        
        if self.path == '/api/entries':
            affected_companies = set()
            
            if USE_MYSQL:
                import pymysql
                conn = pymysql.connect(
                    host=MYSQL_CONFIG["host"],
                    port=MYSQL_CONFIG["port"],
                    user=MYSQL_CONFIG["user"],
                    password=MYSQL_CONFIG["password"],
                    database=MYSQL_CONFIG["database"]
                )
                cursor = conn.cursor()
                
                for entry in data:
                    comp_id = int(entry['company_id'])
                    date_val = entry['date']
                    egg = int(entry.get('egg', 0))
                    veg = int(entry.get('veg', 0))
                    chicken = int(entry.get('chicken', 0))
                    mutton = int(entry.get('mutton', 0))
                    
                    cursor.execute("""
                    INSERT INTO entries (`date`, `company_id`, `egg`, `veg`, `chicken`, `mutton`)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        `egg` = VALUES(`egg`),
                        `veg` = VALUES(`veg`),
                        `chicken` = VALUES(`chicken`),
                        `mutton` = VALUES(`mutton`)
                    """, (date_val, comp_id, egg, veg, chicken, mutton))
                    
                    # Fetch company table name
                    cursor.execute("SELECT `table_name` FROM companies WHERE `id` = %s", (comp_id,))
                    c_row = cursor.fetchone()
                    if c_row:
                        affected_companies.add((comp_id, c_row[0]))
                conn.commit()
                conn.close()
            else:
                conn = sqlite3.connect(DB_FILE)
                cursor = conn.cursor()
                for entry in data:
                    comp_id = int(entry['company_id'])
                    date_val = entry['date']
                    egg = int(entry.get('egg', 0))
                    veg = int(entry.get('veg', 0))
                    chicken = int(entry.get('chicken', 0))
                    mutton = int(entry.get('mutton', 0))
                    
                    cursor.execute("""
                    INSERT INTO entries (date, company_id, egg, veg, chicken, mutton)
                    VALUES (?, ?, ?, ?, ?, ?)
                    ON CONFLICT(date, company_id) DO UPDATE SET
                        egg = excluded.egg,
                        veg = excluded.veg,
                        chicken = excluded.chicken,
                        mutton = excluded.mutton
                    """, (date_val, comp_id, egg, veg, chicken, mutton))
                    
                    # Fetch company details to regenerate files
                    cursor.execute("SELECT filename, table_name FROM companies WHERE id = ?", (comp_id,))
                    c_row = cursor.fetchone()
                    if c_row:
                        affected_companies.add((comp_id, c_row[1]))
                conn.commit()
                conn.close()
                
            # Regenerate the SQL dump files to sync local folder
            for comp_id, table_name in affected_companies:
                # Fetch company filename
                if USE_MYSQL:
                    conn = pymysql.connect(
                        host=MYSQL_CONFIG["host"],
                        port=MYSQL_CONFIG["port"],
                        user=MYSQL_CONFIG["user"],
                        password=MYSQL_CONFIG["password"],
                        database=MYSQL_CONFIG["database"]
                    )
                    cursor = conn.cursor()
                    cursor.execute("SELECT `filename` FROM companies WHERE `id` = %s", (comp_id,))
                    f_row = cursor.fetchone()
                    filename = f_row[0] if f_row else f"{table_name.replace(' ', '_')}.sql"
                    conn.close()
                else:
                    conn = sqlite3.connect(DB_FILE)
                    cursor = conn.cursor()
                    cursor.execute("SELECT filename FROM companies WHERE id = ?", (comp_id,))
                    f_row = cursor.fetchone()
                    filename = f_row[0] if f_row else f"{table_name.replace(' ', '_')}.sql"
                    conn.close()
                    
                regenerate_sql_file(filename, table_name, comp_id)
                
            self._set_headers(200)
            self.wfile.write(json.dumps({"status": "success"}).encode('utf-8'))
            
        elif self.path == '/api/setup':
            if USE_MYSQL:
                import pymysql
                conn = pymysql.connect(
                    host=MYSQL_CONFIG["host"],
                    port=MYSQL_CONFIG["port"],
                    user=MYSQL_CONFIG["user"],
                    password=MYSQL_CONFIG["password"],
                    database=MYSQL_CONFIG["database"]
                )
                cursor = conn.cursor()
                for k, v in data.items():
                    cursor.execute("""
                    INSERT INTO config (`key`, `value`)
                    VALUES (%s, %s)
                    ON DUPLICATE KEY UPDATE `value` = %s
                    """, (k, json.dumps(v), json.dumps(v)))
                conn.commit()
                conn.close()
            else:
                conn = sqlite3.connect(DB_FILE)
                cursor = conn.cursor()
                for k, v in data.items():
                    cursor.execute("""
                    INSERT INTO config (key, value)
                    VALUES (?, ?)
                    ON CONFLICT(key) DO UPDATE SET value = excluded.value
                    """, (k, json.dumps(v)))
                conn.commit()
                conn.close()
                
            self._set_headers(200)
            self.wfile.write(json.dumps({"status": "success"}).encode('utf-8'))
            
        elif self.path == '/api/company':
            name = data['name'].strip()
            since = data.get('since', datetime.now().strftime("%b %Y"))
            filename = make_safe_filename(name)
            table_name = name.lower()
            
            new_id = None
            if USE_MYSQL:
                import pymysql
                conn = pymysql.connect(
                    host=MYSQL_CONFIG["host"],
                    port=MYSQL_CONFIG["port"],
                    user=MYSQL_CONFIG["user"],
                    password=MYSQL_CONFIG["password"],
                    database=MYSQL_CONFIG["database"]
                )
                cursor = conn.cursor()
                cursor.execute("""
                INSERT INTO companies (`name`, `since`, `filename`, `table_name`)
                VALUES (%s, %s, %s, %s)
                """, (name, since, filename, table_name))
                new_id = cursor.lastrowid
                
                # Dynamic Table Creation in MySQL for this new company
                cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS `{table_name}` (
                  `SNO` int(11) NOT NULL AUTO_INCREMENT,
                  `MEAL_TYPE` varchar(50) NOT NULL,
                  `DESCRIPTION` varchar(255) NOT NULL,
                  `NO_OF_PERSONS` int(11) NOT NULL,
                  `DAYS` int(11) NOT NULL,
                  `TOTAL_MEALS` int(11) NOT NULL,
                  `RATE` decimal(10,2) NOT NULL,
                  `AMOUNT` decimal(10,2) NOT NULL,
                  `BILL_MONTH` varchar(50) NOT NULL,
                  PRIMARY KEY (`SNO`)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
                """)
                conn.commit()
                conn.close()
            else:
                conn = sqlite3.connect(DB_FILE)
                cursor = conn.cursor()
                cursor.execute("""
                INSERT INTO companies (name, since, filename, table_name)
                VALUES (?, ?, ?, ?)
                """, (name, since, filename, table_name))
                new_id = cursor.lastrowid
                conn.commit()
                conn.close()
                
            # Create corresponding new empty .sql dump file
            regenerate_sql_file(filename, table_name, new_id)
            
            response = {
                "id": new_id,
                "name": name,
                "since": since,
                "filename": filename,
                "table_name": table_name
            }
            
            self._set_headers(200)
            self.wfile.write(json.dumps(response).encode('utf-8'))
            
        else:
            self._set_headers(404)
            self.wfile.write(json.dumps({"error": "Endpoint not found"}).encode('utf-8'))

if __name__ == '__main__':
    check_mysql_connection()
    init_db()
    handler = APIRequestHandler
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), handler) as httpd:
        print(f"Server started at http://localhost:{PORT}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            pass
        print("Server stopped.")
