import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import os
import plotly.express as px

# --- Page Configuration (ควรเป็นคำสั่งแรกสุด) ---
st.set_page_config(
    page_title="ระบบข้อมูลข้าว",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Inject CSS for Kanit font ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Kanit:wght@300;400;500;700&display=swap');
    html, body, [class*="st-"], .stButton>button, .stTextInput>div>div>input, .stDateInput>div>div>input {
        font-family: 'Kanit', sans-serif !important;
    }
    /* Custom styling for selectbox to ensure Kanit is applied, might need more specific selectors */
    .stSelectbox div[data-baseweb="select"] > div {
        font-family: 'Kanit', sans-serif !important;
    }
    .stMultiSelect div[data-baseweb="select"] > div {
        font-family: 'Kanit', sans-serif !important;
    }
    /* Ensure Kanit for radio button labels */
    .stRadio label span {
        font-family: 'Kanit', sans-serif !important;
    }
    </style>
""", unsafe_allow_html=True)


# --- Configuration ---
DATA_FILE = "rice_data.csv"

DISTRICTS_DATA = {
  "เมืองฉะเชิงเทรา": ["คลองนา", "บางตีนเป็ด", "บางพระ", "บางขวัญ", "บางกระเจ็ด", "บางแก้ว", "บางไผ่", "บ้านใหม่", "ท่าไข่", "วังตะเคียน", "โสธร", "หน้าเมือง", "คลองจุกกระเฌอ", "คลองนครเนื่องเขต", "คลองเปรง", "คลองอุดมชลจร", "คลองหลวงแพ่ง", "ลาดขวาง", "หนามแดง"],
  "บางคล้า": ["บางคล้า", "บางกระเจ็ด", "บางสวน", "บางตลาด", "บางอ้อ", "ปากน้ำ", "หัวไทร", "ท่าทองหลาง", "เสม็ดเหนือ", "เสม็ดใต้"],
  "บางน้ำเปรี้ยว": ["บางน้ำเปรี้ยว", "บางขนาก", "บางกระจับ", "บางครุ", "บางเตย", "บึงน้ำรักษ์", "ดอนเกาะกา", "ดอนฉิมพลี", "หมอนทอง", "โยธะกา", "ศาลาแดง", "สิงโตทอง"],
  "บางปะกง": ["บางปะกง", "บางจาก", "บางครูด", "บางเกลือ", "บางวัว", "บางผึ้ง", "บางสมัคร", "บางแสม", "ท่าข้าม", "ท่าสะอ้าน", "สองคลอง", "หอมศีล"],
  "บ้านโพธิ์": ["บ้านโพธิ์", "คลองขุด", "คลองประเวศ", "คลองบ้านโพธิ์", "ดอนทราย", "บางกรูด", "บางซ่อน", "บางพระ", "บางเตย", "เทพราช", "ท่าพลับ", "สนามจันทร์", "แสนภูดาษ", "หนองตีนนก", "หนองบัว", "สิบเอ็ดศอก", "เกาะไร่"],
  "พนมสารคาม": ["พนมสารคาม", "เกาะขนุน", "เขาหินซ้อน", "ดงน้อย", "ท่าถ่าน", "บ้านซ่อง", "เมืองเก่า", "หนองยาว", "หนองแหน"],
  "ราชสาส์น": ["บางคา", "ดงน้อย", "เมืองใหม่"],
  "สนามชัยเขต": ["คู้ยายหมี", "ทุ่งพระยา", "ท่ากระดาน", "ลาดกระทิง", "หนองไม้งาม"],
  "แปลงยาว": ["แปลงยาว", "วังเย็น", "หัวสำโรง", "หนองไม้แก่น"],
  "ท่าตะเกียบ": ["คลองตะเกรา", "ท่าตะเกียบ"],
  "คลองเขื่อน": ["คลองเขื่อน", "บางตลาด", "บางเล่า", "บางโรง", "ก้อนแก้ว"]
}

COLUMN_NAMES_TH = {
  "TIMESTAMP": "Timestamp บันทึก",
  "REPORT_DATE": "วันที่รายงาน",
  "DISTRICT": "อำเภอ",
  "TAMBON": "ตำบล",
  "RICE_VARIETY": "พันธุ์ข้าว",
  "AREA_RAI": "พื้นที่เพาะปลูก (ไร่)",
  "YIELD_PER_RAI_KG": "ผลผลิตต่อไร่ (กก.)",
  "IRRIGATION_ZONE": "เขตชลประทาน",
  "HARVEST_MONTH": "เดือนที่เก็บเกี่ยว",
  "TOTAL_YIELD_TON": "ปริมาณผลผลิต (ตัน)",
  "ROW_ID": "เลขอ้างอิงการบันทึก"
}

CSV_HEADERS = [
    COLUMN_NAMES_TH["TIMESTAMP"], COLUMN_NAMES_TH["REPORT_DATE"], COLUMN_NAMES_TH["DISTRICT"],
    COLUMN_NAMES_TH["TAMBON"], COLUMN_NAMES_TH["RICE_VARIETY"], COLUMN_NAMES_TH["AREA_RAI"],
    COLUMN_NAMES_TH["YIELD_PER_RAI_KG"], COLUMN_NAMES_TH["IRRIGATION_ZONE"],
    COLUMN_NAMES_TH["HARVEST_MONTH"], COLUMN_NAMES_TH["TOTAL_YIELD_TON"], COLUMN_NAMES_TH["ROW_ID"]
]

RICE_VARIETIES = ["หอมมะลิ", "ปทุมธานี", "ข้าวเจ้าอื่นๆ", "ข้าวเหนียว", "ข้าวสี", "ข้าวอินทรีย์"]
DEFAULT_RICE_VARIETY = "ข้าวเจ้าอื่นๆ"
IRRIGATION_OPTIONS = ["ในเขต", "นอกเขต"]
MONTH_NAMES_TH = ["มกราคม", "กุมภาพันธ์", "มีนาคม", "เมษายน", "พฤษภาคม", "มิถุนายน", "กรกฎาคม", "สิงหาคม", "กันยายน", "ตุลาคม", "พฤศจิกายน", "ธันวาคม"]
MONTH_NUM_TO_NAME_TH = {f"{i+1:02d}": name for i, name in enumerate(MONTH_NAMES_TH)}
MONTH_NAME_TH_TO_NUM = {name: f"{i+1:02d}" for i, name in enumerate(MONTH_NAMES_TH)}


# --- File Data Operations ---
@st.cache_data(ttl=60)
def load_data_for_entry_form(report_date_str, district_name):
    try:
        target_date = datetime.strptime(report_date_str, "%Y-%m-%d").date()
        day_of_month = target_date.day

        if day_of_month not in [15, 25]:
            return {"error": f"ข้อมูลสามารถโหลดได้เฉพาะวันที่ 15 หรือ 25 (โหลดสำหรับ: {target_date.strftime('%d/%m/%Y')})"}

        if not os.path.exists(DATA_FILE):
            return {"success": True, "data": []}

        df = pd.read_csv(DATA_FILE, keep_default_na=False, na_values=[''], dtype=str) # Read all as string initially
        # Convert numeric columns after reading
        numeric_cols_map = {
            COLUMN_NAMES_TH["AREA_RAI"]: float,
            COLUMN_NAMES_TH["YIELD_PER_RAI_KG"]: float,
            COLUMN_NAMES_TH["TOTAL_YIELD_TON"]: float,
            COLUMN_NAMES_TH["ROW_ID"]: pd.Int64Dtype() # Allow integer or NA
        }
        for col, dtype in numeric_cols_map.items():
            if col in df.columns:
                if dtype == float:
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)
                elif dtype == pd.Int64Dtype():
                     df[col] = pd.to_numeric(df[col], errors='coerce').astype(pd.Int64Dtype())


        if COLUMN_NAMES_TH["REPORT_DATE"] not in df.columns or COLUMN_NAMES_TH["DISTRICT"] not in df.columns:
            return {"success": True, "data": []} # Or warning

        def parse_date_robust(val):
            if pd.isna(val) or val == "": return None
            try: return pd.to_datetime(val).date()
            except: return None
        df['parsed_report_date'] = df[COLUMN_NAMES_TH["REPORT_DATE"]].apply(parse_date_robust)

        filtered_df = df[
            (df['parsed_report_date'] == target_date) &
            (df[COLUMN_NAMES_TH["DISTRICT"]] == district_name)
        ]

        data_to_return = []
        for _, row in filtered_df.iterrows():
            entry = {
                "tambon": row.get(COLUMN_NAMES_TH["TAMBON"], ""),
                "variety": row.get(COLUMN_NAMES_TH["RICE_VARIETY"], ""),
                "area": row.get(COLUMN_NAMES_TH["AREA_RAI"], 0.0),
                "yieldPerRai": row.get(COLUMN_NAMES_TH["YIELD_PER_RAI_KG"], 0.0),
                "irrigation": row.get(COLUMN_NAMES_TH["IRRIGATION_ZONE"], ""),
                "harvestMonth": row.get(COLUMN_NAMES_TH["HARVEST_MONTH"], "")
            }
            data_to_return.append(entry)
        return {"success": True, "data": data_to_return}
    except FileNotFoundError: return {"success": True, "data": []}
    except pd.errors.EmptyDataError: return {"success": True, "data": []}
    except Exception as e:
        st.error(f"เกิดข้อผิดพลาดในการโหลดข้อมูลจากไฟล์: {str(e)}")
        return {"error": f"เกิดข้อผิดพลาดในการโหลดข้อมูลจากไฟล์: {str(e)}"}

def save_data_to_file(payload):
    try:
        report_date_str = payload["reportDate"]
        district_name = payload["district"]
        entries_from_client = payload["entries"]
        target_date = datetime.strptime(report_date_str, "%Y-%m-%d").date()
        day_of_month = target_date.day

        if day_of_month not in [15, 25]:
            return {"error": f"ข้อมูลบันทึกได้เฉพาะวันที่ 15 หรือ 25 (บันทึกสำหรับ: {target_date.strftime('%d/%m/%Y')})"}

        existing_df = pd.DataFrame(columns=CSV_HEADERS)
        if os.path.exists(DATA_FILE):
            try:
                existing_df = pd.read_csv(DATA_FILE, keep_default_na=False, na_values=[''], dtype=str)
                if existing_df.empty and os.path.getsize(DATA_FILE) > 0: # File has header but no data
                     existing_df = pd.DataFrame(columns=CSV_HEADERS)
            except pd.errors.EmptyDataError: pass # File is completely empty
        
        if existing_df.empty or not all(h in existing_df.columns for h in CSV_HEADERS):
            existing_df = pd.DataFrame(columns=CSV_HEADERS) # Ensure headers if file was malformed or new

        # Filter out old data for the specific report date and district
        df_to_keep = existing_df.copy() # Start with all existing data
        if not df_to_keep.empty and COLUMN_NAMES_TH["REPORT_DATE"] in df_to_keep.columns and COLUMN_NAMES_TH["DISTRICT"] in df_to_keep.columns:
            def parse_date_robust(val):
                if pd.isna(val) or val == "": return None
                try: return pd.to_datetime(val).date()
                except: return None
            
            # Apply robust parsing for comparison, handling potential NaT from previous step if column was all empty strings
            temp_report_date_series = df_to_keep[COLUMN_NAMES_TH["REPORT_DATE"]].apply(parse_date_robust)

            condition_to_remove = (
                (temp_report_date_series == target_date) &
                (df_to_keep[COLUMN_NAMES_TH["DISTRICT"]] == district_name)
            )
            df_to_keep = df_to_keep[~condition_to_remove]


        new_rows_list = []
        current_timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        report_date_for_file_str = target_date.strftime("%Y-%m-%d")
        
        # Determine next ROW_ID
        max_row_id = 0
        if not df_to_keep.empty and COLUMN_NAMES_TH["ROW_ID"] in df_to_keep.columns:
            # Convert ROW_ID to numeric, coercing errors, then find max. Fill NA with 0 before max.
            numeric_row_ids = pd.to_numeric(df_to_keep[COLUMN_NAMES_TH["ROW_ID"]], errors='coerce').fillna(0)
            if not numeric_row_ids.empty:
                 max_row_id = numeric_row_ids.max()
        next_row_id = int(max_row_id) + 1


        for entry in entries_from_client:
            variety = entry["variety"]
            area_str = entry.get("area", "0.0"); area = float(area_str) if area_str and area_str != "None" else 0.0
            yield_per_rai_str = entry.get("yieldPerRai", "0.0"); yield_per_rai_kg = float(yield_per_rai_str) if yield_per_rai_str and yield_per_rai_str != "None" else 0.0

            if variety and area > 0 and yield_per_rai_kg > 0:
                total_yield_kg = area * yield_per_rai_kg
                total_yield_ton = total_yield_kg / 1000
                new_row_dict = {
                    COLUMN_NAMES_TH["TIMESTAMP"]: current_timestamp_str,
                    COLUMN_NAMES_TH["REPORT_DATE"]: report_date_for_file_str,
                    COLUMN_NAMES_TH["DISTRICT"]: district_name,
                    COLUMN_NAMES_TH["TAMBON"]: entry["tambon"],
                    COLUMN_NAMES_TH["RICE_VARIETY"]: variety,
                    COLUMN_NAMES_TH["AREA_RAI"]: area,
                    COLUMN_NAMES_TH["YIELD_PER_RAI_KG"]: yield_per_rai_kg,
                    COLUMN_NAMES_TH["IRRIGATION_ZONE"]: entry["irrigation"],
                    COLUMN_NAMES_TH["HARVEST_MONTH"]: entry["harvestMonth"],
                    COLUMN_NAMES_TH["TOTAL_YIELD_TON"]: total_yield_ton,
                    COLUMN_NAMES_TH["ROW_ID"]: next_row_id
                }
                new_rows_list.append(new_row_dict)
                next_row_id += 1
        
        updated_df = df_to_keep
        if new_rows_list:
            new_data_df = pd.DataFrame(new_rows_list)
            updated_df = pd.concat([df_to_keep, new_data_df], ignore_index=True)

        # Ensure all columns are present before saving, even if df_to_keep was empty
        if not updated_df.empty:
            for col_header in CSV_HEADERS: # Ensure all expected columns exist, fill with empty string if not
                if col_header not in updated_df.columns:
                    updated_df[col_header] = ""
            updated_df = updated_df.reindex(columns=CSV_HEADERS) # Order columns
            updated_df.to_csv(DATA_FILE, index=False, encoding='utf-8-sig')
        else: # If after all operations, updated_df is empty, write only headers
            pd.DataFrame(columns=CSV_HEADERS).to_csv(DATA_FILE, index=False, encoding='utf-8-sig')

        return {"success": True, "message": f"บันทึกข้อมูลลงไฟล์ {DATA_FILE} สำเร็จ ({len(new_rows_list)} รายการใหม่)"}
    except Exception as e:
        st.error(f"Save to file error: {e}"); import traceback; st.error(traceback.format_exc())
        return {"error": f"เกิดข้อผิดพลาดในการบันทึกข้อมูลลงไฟล์: {str(e)}"}

@st.cache_data(ttl=30)
def load_all_data_from_file_for_view():
    if not os.path.exists(DATA_FILE):
        return pd.DataFrame(columns=CSV_HEADERS)
    try:
        df = pd.read_csv(DATA_FILE, keep_default_na=False, na_values=[''], dtype=str) # Read all as string
        # Convert specific columns to appropriate types for processing and display
        numeric_cols_map = {
            COLUMN_NAMES_TH["AREA_RAI"]: float,
            COLUMN_NAMES_TH["YIELD_PER_RAI_KG"]: float,
            COLUMN_NAMES_TH["TOTAL_YIELD_TON"]: float,
            COLUMN_NAMES_TH["ROW_ID"]: pd.Int64Dtype()
        }
        for col, dtype in numeric_cols_map.items():
            if col in df.columns:
                if dtype == float:
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)
                elif dtype == pd.Int64Dtype():
                     df[col] = pd.to_numeric(df[col], errors='coerce').astype(pd.Int64Dtype())

        if COLUMN_NAMES_TH["REPORT_DATE"] in df.columns:
             df[COLUMN_NAMES_TH["REPORT_DATE"]] = pd.to_datetime(df[COLUMN_NAMES_TH["REPORT_DATE"]], errors='coerce')
        return df
    except pd.errors.EmptyDataError:
        return pd.DataFrame(columns=CSV_HEADERS)
    except Exception as e:
        st.error(f"เกิดข้อผิดพลาดในการโหลดข้อมูลทั้งหมด: {e}")
        return pd.DataFrame(columns=CSV_HEADERS)

# --- Sidebar Navigation ---
with st.sidebar:
    st.title("🌾 ระบบข้อมูลข้าว")
    app_mode = st.sidebar.radio(
        "เลือกหน้าจอ:",
        ("📝 กรอกข้อมูล", "📊 ภาพรวมข้อมูลทั้งหมด"),
        key="app_mode_selector"
    )
    st.sidebar.markdown("---")
    st.caption("สร้างโดย AI (Claude 3)") # ตัวอย่าง Caption

# --- Main App Logic ---
if app_mode == "📝 กรอกข้อมูล":
    st.title("📝 ระบบบันทึกข้อมูลการเพาะปลูกข้าว จังหวัดฉะเชิงเทรา")

    if "selected_district" not in st.session_state: st.session_state.selected_district = None
    if "selected_report_date_str" not in st.session_state: st.session_state.selected_report_date_str = None
    if "tambon_data_entries" not in st.session_state: st.session_state.tambon_data_entries = {}
    if "show_confirmation" not in st.session_state: st.session_state.show_confirmation = False
    if "data_to_confirm" not in st.session_state: st.session_state.data_to_confirm = []

    with st.container(border=True):
        st.subheader("เลือกช่วงเวลาและพื้นที่รายงาน")
        current_year_be = datetime.now().year + 543
        year_options_be = list(range(current_year_be - 2, current_year_be + 3))
        col1, col2, col3, col4 = st.columns(4)
        with col1: selected_year_be = st.selectbox("ปี (พ.ศ.):", year_options_be, index=year_options_be.index(current_year_be), key="sel_year_be_entry")
        with col2:
            selected_month_th = st.selectbox("เดือน:", MONTH_NAMES_TH, index=datetime.now().month -1, key="sel_month_th_entry")
            selected_month_num_str = MONTH_NAME_TH_TO_NUM[selected_month_th]
        with col3: selected_day_str = st.radio("วันที่:", ("15", "25"), horizontal=True, key="sel_day_str_entry")
        with col4:
            district_options = ["-- เลือกอำเภอ --"] + sorted(list(DISTRICTS_DATA.keys()))
            selected_district_input = st.selectbox("อำเภอ:", district_options, key="sel_district_input_entry")

    def process_selection_change_for_entry_form():
        if selected_district_input and selected_district_input != "-- เลือกอำเภอ --":
            st.session_state.selected_district = selected_district_input
            year_ce = selected_year_be - 543
            st.session_state.selected_report_date_str = f"{year_ce}-{selected_month_num_str}-{selected_day_str}"
            with st.spinner(f"กำลังโหลดข้อมูลสำหรับวันที่ {selected_day_str}/{selected_month_num_str}/{selected_year_be} อำเภอ {selected_district_input}..."):
                result = load_data_for_entry_form(st.session_state.selected_report_date_str, st.session_state.selected_district)
            if result.get("error"): st.error(result["error"]); st.session_state.tambon_data_entries = {}
            elif result.get("success"):
                loaded_data_for_ui = result["data"]; new_tambon_entries = {}; tambons_for_district = DISTRICTS_DATA.get(st.session_state.selected_district, [])
                for tambon_name in tambons_for_district:
                    entries_for_this_tambon = [d for d in loaded_data_for_ui if d["tambon"] == tambon_name]
                    if not entries_for_this_tambon: new_tambon_entries[tambon_name] = [{"id": f"{tambon_name}_0_{datetime.now().timestamp()}","variety": DEFAULT_RICE_VARIETY, "area": "", "yieldPerRai": "","irrigation": IRRIGATION_OPTIONS[0], "harvestMonth": MONTH_NAMES_TH[datetime.now().month-1]}]
                    else:
                        new_tambon_entries[tambon_name] = []
                        for i, entry in enumerate(entries_for_this_tambon): new_tambon_entries[tambon_name].append({"id": f"{tambon_name}_{i}_{datetime.now().timestamp()}","variety": entry.get("variety", DEFAULT_RICE_VARIETY),"area": str(entry.get("area", "") if entry.get("area") is not None else ""),"yieldPerRai": str(entry.get("yieldPerRai", "") if entry.get("yieldPerRai") is not None else ""),"irrigation": entry.get("irrigation", IRRIGATION_OPTIONS[0]),"harvestMonth": entry.get("harvestMonth", MONTH_NAMES_TH[datetime.now().month-1])})
                st.session_state.tambon_data_entries = new_tambon_entries; st.success(f"โหลดข้อมูลจากไฟล์สำเร็จ ({len(loaded_data_for_ui)} รายการที่ตรงเงื่อนไข)")
        else: st.session_state.selected_district = None; st.session_state.selected_report_date_str = None; st.session_state.tambon_data_entries = {}

    current_selection_tuple_entry = (selected_year_be, selected_month_num_str, selected_day_str, selected_district_input)
    prev_selection_tuple_entry = st.session_state.get("_previous_selection_tuple_file_entry", None)
    if current_selection_tuple_entry != prev_selection_tuple_entry:
        st.session_state._previous_selection_tuple_file_entry = current_selection_tuple_entry
        if selected_district_input and selected_district_input != "-- เลือกอำเภอ --": process_selection_change_for_entry_form(); st.rerun()
        elif prev_selection_tuple_entry is not None: st.session_state.selected_district = None; st.session_state.selected_report_date_str = None; st.session_state.tambon_data_entries = {}; st.rerun()

    if st.session_state.selected_district and st.session_state.tambon_data_entries:
        st.subheader(f"ข้อมูลรายตำบล: {st.session_state.selected_district}")
        for tambon_name, entries in st.session_state.tambon_data_entries.items():
            with st.expander(f"ตำบล: {tambon_name}", expanded=True):
                cols_header = st.columns([2, 1, 1, 1.5, 1.5, 0.5]); cols_header[0].caption("พันธุ์ข้าว"); cols_header[1].caption("พื้นที่ (ไร่)"); cols_header[2].caption("ผลผลิต/ไร่ (กก.)"); cols_header[3].caption("เขตชลประทาน"); cols_header[4].caption("เดือนเก็บเกี่ยว"); cols_header[5].caption("ดำเนินการ")
                for i, entry_data in enumerate(entries):
                    entry_id = entry_data['id']; cols_entry = st.columns([2, 1, 1, 1.5, 1.5, 0.5])
                    with cols_entry[0]: default_variety_index = RICE_VARIETIES.index(entry_data.get("variety", DEFAULT_RICE_VARIETY)); entries[i]["variety"] = st.selectbox("พันธุ์ข้าว", RICE_VARIETIES, index=default_variety_index, key=f"var_{entry_id}", label_visibility="collapsed")
                    with cols_entry[1]: area_value = entry_data.get("area", ""); area_float = float(area_value) if area_value and area_value not in ["None", ""] else None; entries[i]["area"] = st.number_input("พื้นที่", min_value=0.0, step=0.01, value=area_float, format="%.2f", key=f"area_{entry_id}", label_visibility="collapsed")
                    with cols_entry[2]: yield_value = entry_data.get("yieldPerRai", ""); yield_float = float(yield_value) if yield_value and yield_value not in ["None", ""] else None; entries[i]["yieldPerRai"] = st.number_input("ผลผลิต/ไร่", min_value=0.0, step=0.01, value=yield_float, format="%.2f", key=f"yield_{entry_id}", label_visibility="collapsed")
                    with cols_entry[3]: default_irrigation_index = IRRIGATION_OPTIONS.index(entry_data.get("irrigation", IRRIGATION_OPTIONS[0])); entries[i]["irrigation"] = st.selectbox("เขตฯ", IRRIGATION_OPTIONS,index=default_irrigation_index,key=f"irr_{entry_id}", label_visibility="collapsed")
                    with cols_entry[4]: current_month_index = datetime.now().month -1; default_harvest_index = MONTH_NAMES_TH.index(entry_data.get("harvestMonth", MONTH_NAMES_TH[current_month_index])); entries[i]["harvestMonth"] = st.selectbox("เดือนเก็บเกี่ยว", MONTH_NAMES_TH,index=default_harvest_index,key=f"harv_{entry_id}", label_visibility="collapsed")
                    with cols_entry[5]:
                        if st.button("ลบ", key=f"del_{entry_id}", type="secondary"):
                            st.session_state.tambon_data_entries[tambon_name].pop(i)
                            if not st.session_state.tambon_data_entries[tambon_name]: st.session_state.tambon_data_entries[tambon_name].append({"id": f"{tambon_name}_new_{datetime.now().timestamp()}","variety": DEFAULT_RICE_VARIETY, "area": "", "yieldPerRai": "","irrigation": IRRIGATION_OPTIONS[0], "harvestMonth": MONTH_NAMES_TH[datetime.now().month-1]})
                            st.rerun()
                if st.button(f"+ เพิ่มรายการพันธุ์ข้าว ({tambon_name})", key=f"add_{tambon_name}"):
                    st.session_state.tambon_data_entries[tambon_name].append({"id": f"{tambon_name}_new_{datetime.now().timestamp()}","variety": DEFAULT_RICE_VARIETY, "area": "", "yieldPerRai": "","irrigation": IRRIGATION_OPTIONS[0], "harvestMonth": MONTH_NAMES_TH[datetime.now().month-1]})
                    st.rerun()
    st.divider()
    col_actions1, col_actions2 = st.columns(2)
    with col_actions1:
        if st.button("🔃 ล้าง/โหลดข้อมูลใหม่ในตาราง", use_container_width=True, key="btn_clear_reload_entry"):
            st.session_state._previous_selection_tuple_file_entry = None
            if selected_district_input and selected_district_input != "-- เลือกอำเภอ --": process_selection_change_for_entry_form()
            else: st.session_state.selected_district = None; st.session_state.selected_report_date_str = None; st.session_state.tambon_data_entries = {}
            st.rerun()
    with col_actions2:
        if st.button("🔍 ตรวจสอบและเตรียมบันทึก", type="primary", use_container_width=True, key="btn_validate_entry"):
            if not st.session_state.selected_district or not st.session_state.selected_report_date_str: st.error("กรุณาเลือกปี เดือน วันที่ และอำเภอให้ครบถ้วน")
            else:
                all_entries_to_confirm = []; is_valid = True; has_actual_data = False
                for tambon_name, entries_list in st.session_state.tambon_data_entries.items():
                    for i, entry_dict in enumerate(entries_list):
                        variety = entry_dict.get("variety", DEFAULT_RICE_VARIETY)
                        try: area = float(entry_dict.get("area") if entry_dict.get("area") not in [None, ""] else "0.0")
                        except ValueError: area = 0.0
                        try: yield_val = float(entry_dict.get("yieldPerRai") if entry_dict.get("yieldPerRai") not in [None, ""] else "0.0")
                        except ValueError: yield_val = 0.0

                        if variety:
                            if area < 0 : st.error(f"[{tambon_name}] แถวที่ {i+1}: พื้นที่ฯ ต้องไม่ติดลบ"); is_valid = False; break
                            if yield_val < 0: st.error(f"[{tambon_name}] แถวที่ {i+1}: ผลผลิต/ไร่ฯ ต้องไม่ติดลบ"); is_valid = False; break
                            if area > 0 and yield_val <= 0: st.error(f"[{tambon_name}] แถวที่ {i+1}: หากมีพื้นที่ ({area:.2f} ไร่) ผลผลิต/ไร่ฯ ต้องมากกว่า 0"); is_valid = False; break
                            if yield_val > 0 and area <= 0: st.error(f"[{tambon_name}] แถวที่ {i+1}: หากมีผลผลิต/ไร่ ({yield_val:.2f} กก.) พื้นที่ฯ ต้องมากกว่า 0"); is_valid = False; break
                            all_entries_to_confirm.append({"tambon": tambon_name, "id": entry_dict["id"], "variety": variety, "area": str(area),"yieldPerRai": str(yield_val),"irrigation": entry_dict.get("irrigation", IRRIGATION_OPTIONS[0]),"harvestMonth": entry_dict.get("harvestMonth", MONTH_NAMES_TH[0])})
                            if area > 0 and yield_val > 0: has_actual_data = True
                    if not is_valid: break
                if is_valid:
                    if not all_entries_to_confirm: st.warning("ไม่มีรายการข้อมูลใดๆ หากดำเนินการต่อ ข้อมูลเก่าจะถูกลบ (ถ้ามี)")
                    elif not has_actual_data: st.warning("ทุกรายการมีพื้นที่หรือผลผลิตเป็น 0 หากดำเนินการต่อ ข้อมูลเก่าจะถูกลบ และไม่มีรายการใหม่บันทึก")
                    st.session_state.data_to_confirm = all_entries_to_confirm; st.session_state.show_confirmation = True; st.rerun()
    if st.session_state.show_confirmation:
        with st.container(border=True):
            st.subheader("สรุปข้อมูลก่อนบันทึก")
            if st.session_state.selected_report_date_str: year_ce_conf = int(st.session_state.selected_report_date_str.split("-")[0]); month_conf = st.session_state.selected_report_date_str.split("-")[1]; day_conf = st.session_state.selected_report_date_str.split("-")[2]; year_be_conf = year_ce_conf + 543; st.markdown(f"**วันที่รายงาน:** {day_conf}/{month_conf}/{year_be_conf}")
            else: st.markdown("**วันที่รายงาน:** (ไม่ได้เลือก)")
            st.markdown(f"**อำเภอ:** {st.session_state.selected_district or '(ไม่ได้เลือก)'}")
            if st.session_state.data_to_confirm:
                confirm_df_data = []
                for entry in st.session_state.data_to_confirm:
                    area_c = float(entry.get('area') or 0.0); yield_c = float(entry.get('yieldPerRai') or 0.0)
                    if area_c > 0 and yield_c > 0: confirm_df_data.append({"ตำบล": entry["tambon"],"พันธุ์ข้าว": entry["variety"],"พื้นที่ (ไร่)": f"{area_c:.2f}","ผลผลิต/ไร่ (กก.)": f"{yield_c:.2f}","เขตชลประทาน": entry["irrigation"],"เดือนเก็บเกี่ยว": entry["harvestMonth"]})
                if confirm_df_data: st.dataframe(pd.DataFrame(confirm_df_data), use_container_width=True, hide_index=True)
                else: st.info("ไม่มีข้อมูลที่สมบูรณ์ที่จะบันทึก (ข้อมูลเก่าในไฟล์สำหรับวันที่และอำเภอนี้จะถูกลบ)")
            else: st.info("ไม่มีข้อมูลที่จะบันทึก (ข้อมูลเก่าในไฟล์สำหรับวันที่และอำเภอนี้จะถูกลบ)")
            confirm_cols = st.columns(2)
            with confirm_cols[0]:
                if st.button("แก้ไขข้อมูล", use_container_width=True, key="btn_edit_confirm_entry"): st.session_state.show_confirmation = False; st.rerun()
            with confirm_cols[1]:
                if st.button("✅ ยืนยันการบันทึก", type="primary", use_container_width=True, key="btn_save_confirm_entry"):
                    payload_to_save_file = {"reportDate": st.session_state.selected_report_date_str,"district": st.session_state.selected_district,"entries": st.session_state.data_to_confirm}
                    with st.spinner("กำลังบันทึกข้อมูลลงไฟล์..."): save_result = save_data_to_file(payload_to_save_file)
                    if save_result.get("success"):
                        st.success(save_result["message"]); st.session_state.show_confirmation = False; st.session_state._previous_selection_tuple_file_entry = None
                        if selected_district_input and selected_district_input != "-- เลือกอำเภอ --": process_selection_change_for_entry_form()
                        st.rerun()
                    else: st.error(save_result.get("error", "เกิดข้อผิดพลาดไม่ทราบสาเหตุในการบันทึก"))


elif app_mode == "📊 ภาพรวมข้อมูลทั้งหมด":
    st.title("📊 ภาพรวมข้อมูลการเพาะปลูกข้าวทั้งหมด")

    df_all_data_raw = load_all_data_from_file_for_view()

    if df_all_data_raw.empty:
        st.info(f"ยังไม่มีข้อมูลในไฟล์ {DATA_FILE} หรือไฟล์ยังไม่ได้ถูกสร้าง")
    else:
        st.write(f"พบข้อมูลทั้งหมด {len(df_all_data_raw)} แถว (ก่อนกรอง):")
        df_view = df_all_data_raw.copy()

        st.markdown("---")
        st.subheader("ตัวกรองข้อมูล:")

        if COLUMN_NAMES_TH["REPORT_DATE"] in df_view.columns and not pd.api.types.is_datetime64_any_dtype(df_view[COLUMN_NAMES_TH["REPORT_DATE"]]):
            df_view[COLUMN_NAMES_TH["REPORT_DATE"]] = pd.to_datetime(df_view[COLUMN_NAMES_TH["REPORT_DATE"]], errors='coerce')
        df_view = df_view.dropna(subset=[COLUMN_NAMES_TH["REPORT_DATE"]]).copy()

        if not df_view.empty:
            df_view['ปี พ.ศ. (รายงาน)'] = df_view[COLUMN_NAMES_TH["REPORT_DATE"]].dt.year + 543
            df_view['เดือนตัวเลข (รายงาน)'] = df_view[COLUMN_NAMES_TH["REPORT_DATE"]].dt.month
            df_view['เดือน (รายงาน)'] = df_view[COLUMN_NAMES_TH["REPORT_DATE"]].dt.strftime('%m').map(MONTH_NUM_TO_NAME_TH)

        date_filter_cols = st.columns(2)
        min_date_avail = df_view[COLUMN_NAMES_TH["REPORT_DATE"]].min().date() if not df_view.empty and COLUMN_NAMES_TH["REPORT_DATE"] in df_view.columns and not df_view[COLUMN_NAMES_TH["REPORT_DATE"]].isna().all() else date.today() - timedelta(days=365)
        max_date_avail = df_view[COLUMN_NAMES_TH["REPORT_DATE"]].max().date() if not df_view.empty and COLUMN_NAMES_TH["REPORT_DATE"] in df_view.columns and not df_view[COLUMN_NAMES_TH["REPORT_DATE"]].isna().all() else date.today()
        
        start_date = date_filter_cols[0].date_input("วันที่เริ่มต้น:", min_date_avail, min_value=min_date_avail, max_value=max_date_avail, key="view_start_date")
        end_date = date_filter_cols[1].date_input("วันที่สิ้นสุด:", max_date_avail, min_value=start_date if start_date else min_date_avail, max_value=max_date_avail, key="view_end_date")

        filter_cols = st.columns([1, 1, 2])
        unique_years_be = sorted(df_view['ปี พ.ศ. (รายงาน)'].dropna().unique(), reverse=True) if 'ปี พ.ศ. (รายงาน)' in df_view else []
        selected_filter_years = filter_cols[0].multiselect("เลือกปี พ.ศ.:", unique_years_be, default=unique_years_be, key="filter_years_view")

        unique_months_ordered = []
        if 'เดือนตัวเลข (รายงาน)' in df_view.columns and 'เดือน (รายงาน)' in df_view.columns and not df_view['เดือนตัวเลข (รายงาน)'].dropna().empty:
            month_map = df_view[['เดือนตัวเลข (รายงาน)', 'เดือน (รายงาน)']].dropna().drop_duplicates().sort_values('เดือนตัวเลข (รายงาน)')
            unique_months_ordered = month_map['เดือน (รายงาน)'].tolist()
        selected_filter_months = filter_cols[1].multiselect("เลือกเดือน:", unique_months_ordered, default=unique_months_ordered, key="filter_months_view")

        unique_districts = sorted(df_view[COLUMN_NAMES_TH["DISTRICT"]].dropna().unique()) if COLUMN_NAMES_TH["DISTRICT"] in df_view else []
        selected_filter_districts = filter_cols[2].multiselect("เลือกอำเภอ:", unique_districts, default=unique_districts, key="filter_districts_view")

        df_filtered_for_display = df_view.copy()
        if start_date and end_date and COLUMN_NAMES_TH["REPORT_DATE"] in df_filtered_for_display.columns:
            df_filtered_for_display = df_filtered_for_display[(df_filtered_for_display[COLUMN_NAMES_TH["REPORT_DATE"]].dt.date >= start_date) & (df_filtered_for_display[COLUMN_NAMES_TH["REPORT_DATE"]].dt.date <= end_date)]
        if selected_filter_years and 'ปี พ.ศ. (รายงาน)' in df_filtered_for_display.columns:
            df_filtered_for_display = df_filtered_for_display[df_filtered_for_display['ปี พ.ศ. (รายงาน)'].isin(selected_filter_years)]
        if selected_filter_months and 'เดือน (รายงาน)' in df_filtered_for_display.columns:
            df_filtered_for_display = df_filtered_for_display[df_filtered_for_display['เดือน (รายงาน)'].isin(selected_filter_months)]
        if selected_filter_districts and COLUMN_NAMES_TH["DISTRICT"] in df_filtered_for_display.columns:
            df_filtered_for_display = df_filtered_for_display[df_filtered_for_display[COLUMN_NAMES_TH["DISTRICT"]].isin(selected_filter_districts)]

        st.markdown("---")
        st.subheader("ตารางข้อมูล (หลังการกรอง):")

        if df_filtered_for_display.empty:
            st.info("ไม่พบข้อมูลตามเงื่อนไขที่เลือก")
        else:
            st.write(f"แสดงข้อมูล {len(df_filtered_for_display)} แถว:")
            cols_to_display_in_table = [col for col in CSV_HEADERS if col != COLUMN_NAMES_TH["TIMESTAMP"]]
            df_final_display = df_filtered_for_display.copy() # Start with filtered data
            
            # Ensure all desired display columns exist, even if empty
            for col_header in cols_to_display_in_table:
                if col_header not in df_final_display.columns:
                    df_final_display[col_header] = "" # or pd.NA or None depending on desired display

            df_final_display = df_final_display[cols_to_display_in_table] # Select and order


            if COLUMN_NAMES_TH["REPORT_DATE"] in df_final_display.columns:
                df_final_display[COLUMN_NAMES_TH["REPORT_DATE"]] = pd.to_datetime(df_final_display[COLUMN_NAMES_TH["REPORT_DATE"]], errors='coerce').dt.strftime('%d/%m/') + (pd.to_datetime(df_final_display[COLUMN_NAMES_TH["REPORT_DATE"]], errors='coerce').dt.year + 543).astype(str)
                df_final_display[COLUMN_NAMES_TH["REPORT_DATE"]] = df_final_display[COLUMN_NAMES_TH["REPORT_DATE"]].replace('NaT/NaT', '', regex=False) # Clean up NaT if any

            # Format numeric columns for display
            for col_name in [COLUMN_NAMES_TH["AREA_RAI"], COLUMN_NAMES_TH["YIELD_PER_RAI_KG"]]:
                if col_name in df_final_display.columns:
                    df_final_display[col_name] = pd.to_numeric(df_final_display[col_name], errors='coerce').fillna(0).apply(lambda x: f"{x:,.2f}")
            if COLUMN_NAMES_TH["TOTAL_YIELD_TON"] in df_final_display.columns:
                df_final_display[COLUMN_NAMES_TH["TOTAL_YIELD_TON"]] = pd.to_numeric(df_final_display[COLUMN_NAMES_TH["TOTAL_YIELD_TON"]], errors='coerce').fillna(0).apply(lambda x: f"{x:,.3f}")


            st.dataframe(df_final_display, use_container_width=True, hide_index=True, height=400)

            total_area_display = pd.to_numeric(df_filtered_for_display[COLUMN_NAMES_TH["AREA_RAI"]], errors='coerce').sum()
            total_yield_ton_display = pd.to_numeric(df_filtered_for_display[COLUMN_NAMES_TH["TOTAL_YIELD_TON"]], errors='coerce').sum()
            
            st.markdown(f"""
            <div style="text-align: right; font-weight: bold; margin-top: 10px;">
                ผลรวมพื้นที่เพาะปลูก (ไร่): {total_area_display:,.2f} | 
                ผลรวมปริมาณผลผลิต (ตัน): {total_yield_ton_display:,.3f}
            </div>
            """, unsafe_allow_html=True)

            # --- ตารางสรุปรายอำเภอและชนิดข้าว ---
            st.markdown("---")
            st.subheader("ตารางสรุป: พื้นที่และผลผลิต แยกตามอำเภอและชนิดข้าว")

            if not df_filtered_for_display.empty:
                df_summary_district_variety = df_filtered_for_display.groupby(
                    [COLUMN_NAMES_TH["DISTRICT"], COLUMN_NAMES_TH["RICE_VARIETY"]],
                    as_index=False # สำคัญเพื่อให้ group keys เป็นคอลัมน์
                ).agg(
                    # ใช้ชื่อคอลัมน์ชั่วคราวที่ยังไม่ได้เปลี่ยนชื่อ เพื่อให้ sum() ง่าย
                    # แล้วค่อย rename ทีหลัง
                    temp_area_sum=(COLUMN_NAMES_TH["AREA_RAI"], 'sum'),
                    temp_yield_sum=(COLUMN_NAMES_TH["TOTAL_YIELD_TON"], 'sum')
                )

                # คำนวณผลรวมจากคอลัมน์ตัวเลข **ก่อน** ที่จะ rename หรือ format เป็น string
                if not df_summary_district_variety.empty:
                    overall_summary_area = df_summary_district_variety["temp_area_sum"].sum()
                    overall_summary_yield = df_summary_district_variety["temp_yield_sum"].sum()
                else:
                    overall_summary_area = 0.0
                    overall_summary_yield = 0.0

                # เปลี่ยนชื่อคอลัมน์ใน DataFrame สรุปให้เป็นภาษาไทยสวยงาม
                df_summary_district_variety.rename(columns={
                    COLUMN_NAMES_TH["DISTRICT"]: "อำเภอ",
                    COLUMN_NAMES_TH["RICE_VARIETY"]: "ชนิดข้าว",
                    "temp_area_sum": "พื้นที่รวม (ไร่)", # เปลี่ยนจากชื่อชั่วคราว
                    "temp_yield_sum": "ผลผลิตรวม (ตัน)"  # เปลี่ยนจากชื่อชั่วคราว
                }, inplace=True)
                
                # ทำสำเนา DataFrame สำหรับแสดงผล (เพื่อไม่ให้กระทบการคำนวณผลรวม)
                df_summary_display = df_summary_district_variety.copy()

                # จัดรูปแบบตัวเลขใน DataFrame ที่จะแสดงผล
                if not df_summary_display.empty:
                    df_summary_display["พื้นที่รวม (ไร่)"] = df_summary_display["พื้นที่รวม (ไร่)"].apply(lambda x: f"{x:,.2f}")
                    df_summary_display["ผลผลิตรวม (ตัน)"] = df_summary_display["ผลผลิตรวม (ตัน)"].apply(lambda x: f"{x:,.3f}")

                if not df_summary_display.empty:
                    st.dataframe(
                        df_summary_display,
                        use_container_width=True,
                        hide_index=True,
                        column_order=("อำเภอ", "ชนิดข้าว", "พื้นที่รวม (ไร่)", "ผลผลิตรวม (ตัน)")
                    )
                    
                    # --- เพิ่มผลรวมสำหรับตารางสรุป ---
                    st.markdown(f"""
                    <div style="text-align: right; font-weight: bold; margin-top: 10px;">
                        ผลรวมทั้งหมดของตารางสรุป: พื้นที่เพาะปลูก (ไร่): {overall_summary_area:,.2f} | 
                        ผลรวมปริมาณผลผลิต (ตัน): {overall_summary_yield:,.3f}
                    </div>
                    """, unsafe_allow_html=True)
                    # --- สิ้นสุดการเพิ่มผลรวมสำหรับตารางสรุป ---

                else:
                    st.info("ไม่มีข้อมูลสรุปสำหรับแสดงผลตามเงื่อนไขการกรองปัจจุบัน")
            else:
                st.info("ไม่มีข้อมูลสำหรับสร้างตารางสรุป (ข้อมูลที่กรองว่างเปล่า)")

            # --- กราฟ (คนละบรรทัด) ---
            st.markdown("---")
            st.subheader("กราฟแสดงผล (จากข้อมูลที่กรอง):")

            # 1. กราฟแท่ง: พื้นที่เพาะปลูกรวม (ไร่) รายอำเภอ (แบ่งตามชนิดข้าว)
            if not df_filtered_for_display.empty and \
               COLUMN_NAMES_TH["DISTRICT"] in df_filtered_for_display.columns and \
               COLUMN_NAMES_TH["RICE_VARIETY"] in df_filtered_for_display.columns and \
               COLUMN_NAMES_TH["AREA_RAI"] in df_filtered_for_display.columns:
                df_bar_area_by_variety = df_filtered_for_display.groupby(
                    [COLUMN_NAMES_TH["DISTRICT"], COLUMN_NAMES_TH["RICE_VARIETY"]],as_index=False
                )[COLUMN_NAMES_TH["AREA_RAI"]].sum()
                if not df_bar_area_by_variety.empty:
                    fig_bar_district_area = px.bar(df_bar_area_by_variety,
                        x=COLUMN_NAMES_TH["DISTRICT"], y=COLUMN_NAMES_TH["AREA_RAI"],
                        color=COLUMN_NAMES_TH["RICE_VARIETY"], title="พื้นที่เพาะปลูกรวม (ไร่) รายอำเภอ (แบ่งตามชนิดข้าว)",
                        labels={COLUMN_NAMES_TH["AREA_RAI"]: "พื้นที่รวม (ไร่)", COLUMN_NAMES_TH["DISTRICT"]: "อำเภอ", COLUMN_NAMES_TH["RICE_VARIETY"]: "ชนิดข้าว"},
                        barmode='stack')
                    fig_bar_district_area.update_layout(xaxis_title="อำเภอ", yaxis_title="พื้นที่รวม (ไร่)")
                    st.plotly_chart(fig_bar_district_area, use_container_width=True)
                else: st.info("ไม่มีข้อมูลสำหรับกราฟพื้นที่เพาะปลูกรายอำเภอ/ชนิดข้าว")
            else: st.info("ข้อมูลไม่เพียงพอสำหรับกราฟพื้นที่เพาะปลูกรายอำเภอ")

            st.markdown("---") # คั่นระหว่างกราฟ

            # 2. กราฟวงกลม: สัดส่วนผลผลิตตามชนิดข้าว
            if not df_filtered_for_display.empty and \
               COLUMN_NAMES_TH["RICE_VARIETY"] in df_filtered_for_display.columns and \
               COLUMN_NAMES_TH["TOTAL_YIELD_TON"] in df_filtered_for_display.columns:
                df_pie_variety = df_filtered_for_display.groupby(COLUMN_NAMES_TH["RICE_VARIETY"], as_index=False)[COLUMN_NAMES_TH["TOTAL_YIELD_TON"]].sum()
                df_pie_variety = df_pie_variety[df_pie_variety[COLUMN_NAMES_TH["TOTAL_YIELD_TON"]] > 0]
                if not df_pie_variety.empty:
                    fig_pie_variety = px.pie(df_pie_variety, values=COLUMN_NAMES_TH["TOTAL_YIELD_TON"], names=COLUMN_NAMES_TH["RICE_VARIETY"],
                                             title="สัดส่วนผลผลิต (ตัน) ตามชนิดข้าว",
                                             labels={COLUMN_NAMES_TH["TOTAL_YIELD_TON"]: "ผลผลิตรวม (ตัน)", COLUMN_NAMES_TH["RICE_VARIETY"]: "ชนิดข้าว"})
                    fig_pie_variety.update_traces(textposition='inside', textinfo='percent+label')
                    st.plotly_chart(fig_pie_variety, use_container_width=True)
                else: st.info("ไม่มีข้อมูลสำหรับกราฟสัดส่วนชนิดข้าว")
            else: st.info("ข้อมูลไม่เพียงพอสำหรับกราฟชนิดข้าว")

            # --- ปุ่มสำหรับดาวน์โหลดข้อมูลที่แสดง ---
            if not df_filtered_for_display.empty:
                @st.cache_data
                def convert_df_to_csv_view(df_to_convert):
                    return df_to_convert.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
                csv_download_view = convert_df_to_csv_view(df_final_display) # ใช้ df_final_display ที่จัดรูปแบบแล้ว
                current_time_str_view = datetime.now().strftime("%Y%m%d_%H%M%S")
                st.download_button(
                    label="📥 ดาวน์โหลดข้อมูลที่แสดง (CSV)", data=csv_download_view,
                    file_name=f"rice_data_export_view_{current_time_str_view}.csv", mime="text/csv",
                    key="download_csv_overview_page"
                )