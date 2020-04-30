import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from data_model import Lab, Site

# If modifying these scopes, delete the file token.pickle.
SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]


def _get_sheet(sheet_id, sheet_range, sheet_name=None):
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists("env/token.pickle"):
        with open("env/token.pickle", "rb") as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "env/credentials.json", SCOPES
            )
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open("env/token.pickle", "wb") as token:
            pickle.dump(creds, token)

    service = build("sheets", "v4", credentials=creds, cache_discovery=False)

    # Call the Sheets API
    sheet = service.spreadsheets()
    header_range = "A1:X1" if sheet_name is None else "{}!A1:X1".format(sheet_name)
    if sheet_name is not None:
        sheet_range = "{}!{}".format(sheet_name, sheet_range)

    header = sheet.values().get(spreadsheetId=sheet_id, range=header_range).execute()
    result = sheet.values().get(spreadsheetId=sheet_id, range=sheet_range).execute()
    values = result.get("values", [])
    header = header.get("values", [])
    return header, values


def read_lab_coding(labs):
    LAB_CODING_ID = "1iF3n-3THYrThApOoscJBykN7vbEyJdiFKAaz11DHUW4"
    SITE_CODE_COL = "SiteCode"
    LAB_CODE_COL = "LabCode"
    CODING_PASS_COL = "Coding pass"
    LAB_CODING_RANGE = "A2:X"
    header, values = _get_sheet(LAB_CODING_ID, LAB_CODING_RANGE, "CodingSites")

    labs_dict = {l.lab_code: l for l in labs}
    for row in header:
        print(row)
        for i, col in enumerate(row):
            print(i, col)
            if col == SITE_CODE_COL:
                SITE_CODE_COL = i
            if col == LAB_CODE_COL:
                LAB_CODE_COL = i
            if col == CODING_PASS_COL:
                CODING_PASS_COL = i

    if not values:
        print("No data found.")
    else:
        for row in values:
            try:
                print("%s, %s" % (row[LAB_CODE_COL], row[CODING_PASS_COL]))
                site_code = row[SITE_CODE_COL]
                lab_code = row[LAB_CODE_COL]
                coding_pass = row[CODING_PASS_COL]
                if coding_pass == "Communication & Gesture":
                    labs_dict[lab_code].code_comm = True
                if coding_pass == "Emotion":
                    labs_dict[lab_code].code_emo = True
                if coding_pass == "Locomotion":
                    labs_dict[lab_code].code_loc = True
                if coding_pass == "Object":
                    labs_dict[lab_code].code_obj = True
            except:
                print("ERROR in CODING PASS ROW:", row)
                continue
    header, values = _get_sheet(LAB_CODING_ID, "A1:A", "TranscribersList")
    tra_names = []
    # The function above assumes a header, but this sheet does not have one
    for row in header:
        tra_names.append(row[0])
    for row in values:
        tra_names.append(row[0])
    return labs, tra_names


def read_master():
    """Shows basic usage of the Sheets API.
    Prints values from a sample spreadsheet.
    """
    # The ID and range of a sample spreadsheet.
    PLAY_MASTER_ID = "1V9RuZJNRN4lehLzRSWO0MqVclsXPw7Z-Lxq-VQOvM-A"
    PLAY_MASTER_RANGE = "A2:X"
    PLAY_MASTER_NAME = "SiteTracking"
    SITE_CODE_COL = "SiteCode"
    LAB_CODE_COL = "LabCode"
    EMAIL_COL = "email"
    INST_COL = "Institution"
    PI_COL = "PI_Fullname"
    ROLE_COL = "Role"

    header, values = _get_sheet(PLAY_MASTER_ID, PLAY_MASTER_RANGE, PLAY_MASTER_NAME)

    for row in header:
        for i, col in enumerate(row):
            if col == SITE_CODE_COL:
                SITE_CODE_COL = i
            if col == LAB_CODE_COL:
                LAB_CODE_COL = i
            if col == EMAIL_COL:
                EMAIL_COL = i
            if col == INST_COL:
                INST_COL = i
            if col == PI_COL:
                PI_COL = i
            if col == ROLE_COL:
                ROLE_COL = i

    if not values:
        print("No data found.")
    else:
        labs = []
        sites = {}
        for row in values:
            print("%s, %s" % (row[INST_COL], row[LAB_CODE_COL]))
            site_code = row[SITE_CODE_COL]
            lab_code = row[LAB_CODE_COL]
            try:
                email = row[EMAIL_COL]
            except IndexError:
                email = "No email listed"
            inst = row[INST_COL]
            try:
                pi = row[PI_COL]
            except:
                pi = "No PI listed"
            role = row[ROLE_COL]
            if site_code not in sites:
                sites[site_code] = Site(site_code)
            if "Coding" in role:
                lab = Lab(site_code, lab_code, pi, email, inst)
                sites[site_code].labs[lab_code] = lab
                labs.append(lab)
        labs, tra_names = read_lab_coding(labs)
        return sites, labs, tra_names


if __name__ == "__main__":
    read_master()
