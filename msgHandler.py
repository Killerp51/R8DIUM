import datetime
import random
import string
import dbAccess
from r8udbBotInclude import DB_FILENAME



def generate_password(length=20,
                      lowercase=True,
                      uppercase=True,
                      numbers=True,
                      special=True):
    chars = []
    if lowercase:
        chars += string.ascii_lowercase
    if uppercase:
        chars += string.ascii_uppercase
    if numbers:
        chars += string.digits
    if special:
        chars += string.punctuation
    pw = random.choices(chars, k=length)
    return ''.join(pw)


def days_elapsed(d1: datetime.date, d2: datetime.date) -> int:
    return (d1-d2).days


def check_ban_status(sid, ldb):
    ban_date = dbAccess.get_element(sid, dbAccess.sid, dbAccess.ban_date, ldb)
    ban_duration = dbAccess.get_element(sid, dbAccess.sid, dbAccess.ban_duration, ldb)
    bdate = datetime.datetime.strptime(ban_date, '%m/%d/%y')
    if (datetime.datetime.today() - bdate).days < int(ban_duration):
        return True
    else:
        return False


def read_field(sid, field_name, ldb):
    if field_name not in dbAccess.db_field_list:
        return f'[r8udbBot: FIELD ERROR] field: "{field_name}" unknown'
    if int(dbAccess.get_element(sid, dbAccess.sid, dbAccess.sid, ldb)) < 0:
        return f'[r8udbBot: INDEX ERROR] SID "{sid}" not found'
    return dbAccess.get_element(sid, dbAccess.sid, field_name, ldb)


def write_field(sid, field_name, write_val, ldb):
    if field_name not in dbAccess.db_field_list:
        return f'[r8udbBot: FIELD ERROR] field: "{field_name}" unknown'
    if int(dbAccess.get_element(sid, dbAccess.sid, dbAccess.sid, ldb)) < 0:
        return f'[r8udbBot: INDEX ERROR] SID "{sid}" not found'
    if int(dbAccess.set_element(sid, dbAccess.sid, field_name, write_val, ldb)) > 0:
        dbAccess.save_db(DB_FILENAME, ldb)
        return write_val
    else:
        return f'[r8udbBot: WRITE ERROR] unknown failure to write to field: {field_name}'


def add_user(name, ldb):
    if dbAccess.get_element(name,dbAccess.discord_name,dbAccess.sid,ldb) != -1:
        return f'[r8udbBot: NAME ERROR] Discord name "{name}" already exists'
    new_sid = dbAccess.add_new_user(name, ldb)
    new_pass = generate_password(random.randint(15, 25))
    join_date = datetime.date.today().strftime('%#m/%#d/%y')
    dbAccess.set_element(new_sid, dbAccess.sid, dbAccess.password, new_pass, ldb)
    dbAccess.set_element(new_sid, dbAccess.sid, dbAccess.join_date, join_date, ldb)
    dbAccess.set_element(new_sid, dbAccess.sid, dbAccess.banned, False, ldb)
    dbAccess.save_db(DB_FILENAME, ldb)
    return f'{name} (SID: {new_sid}) added on {join_date}, pass: {new_pass}'


def delete_user(sid, ldb):
    if int(dbAccess.get_element(sid, dbAccess.sid, dbAccess.sid, ldb)) < 0:
        return f'[r8udbBot: INDEX ERROR] SID "{sid}" not found'
    if dbAccess.del_user(sid, ldb) < 0:
        return f'[r8udbBot: UNK ERROR] in delete user routine'
    dbAccess.save_db(DB_FILENAME, ldb)
    return f'User sid: {sid} deleted'


def add_note(sid, note, ldb):
    if int(dbAccess.get_element(sid, dbAccess.sid, dbAccess.sid, ldb)) < 0:
        return f'[r8udbBot: INDEX ERROR] SID "{sid}" not found'
    curr_note = dbAccess.get_element(sid, dbAccess.sid, dbAccess.notes, ldb)
    if curr_note:
        update = curr_note + '|' + str(note)
        dbAccess.set_element(sid, dbAccess.sid, dbAccess.notes, update, ldb)
    else:
        dbAccess.set_element(sid, dbAccess.sid, dbAccess.notes, str(note), ldb)
    dbAccess.save_db(DB_FILENAME, ldb)
    return f'Note: "{note}" added to user: {dbAccess.get_element(sid, dbAccess.sid, dbAccess.discord_name, ldb)}'


def ban_user(sid, duration, reason, ldb):
    if int(dbAccess.get_element(sid, dbAccess.sid, dbAccess.sid, ldb)) < 0:
        return f'[r8udbBot: INDEX ERROR] SID "{sid}" not found'
    ban_date = datetime.date.today().strftime('%#m/%#d/%y')
    # ban_date = datetime.date.today()
    dbAccess.set_element(sid, dbAccess.sid, dbAccess.banned, True, ldb)
    dbAccess.set_element(sid, dbAccess.sid, dbAccess.ban_date, ban_date, ldb)
    dbAccess.set_element(sid, dbAccess.sid, dbAccess.ban_duration, duration, ldb)
    dbAccess.set_element(sid, dbAccess.sid, dbAccess.password, generate_password(random.randint(15, 25)), ldb)
    add_note(sid, f'Banned ({ban_date}) for {duration} days - {reason}', ldb)
    dbAccess.save_db(DB_FILENAME, ldb)
    return (f'User "{dbAccess.get_element(sid,dbAccess.sid,dbAccess.discord_name, ldb)}" '
            f'[SID: {sid}]) **Banned** and password changed')


def unban_user(sid, admin_name, ldb):
    if int(dbAccess.get_element(sid, dbAccess.sid, dbAccess.sid, ldb)) < 0:
        return f'[r8udbBot: INDEX ERROR] SID "{sid}" not found'
    current_date = datetime.date.today().strftime('%#m/%#d/%y')
    dbAccess.set_element(sid, dbAccess.sid, dbAccess.banned, False, ldb)
    dbAccess.set_element(sid, dbAccess.sid, dbAccess.ban_date, '', ldb)
    dbAccess.set_element(sid, dbAccess.sid, dbAccess.ban_duration, '', ldb)
    add_note(sid, f'UNbanned ({current_date}) by {admin_name}', ldb)
    dbAccess.save_db(DB_FILENAME, ldb)
    return (f'User "{dbAccess.get_element(sid,dbAccess.sid,dbAccess.discord_name, ldb)}" '
            f'[SID: {sid}]) **Unbanned**')


def list_users(ldb):
    return_str = ''
    for record in ldb:
        return_str += f'[{record[dbAccess.sid]}] : {record[dbAccess.discord_name]} / {record[dbAccess.run8_name]}'
        if record[dbAccess.banned] == 'True':
            return_str += f' **--> BANNED on {record[dbAccess.ban_date]} for {record[dbAccess.ban_duration]} days <--**'
        return_str += '\n'
    return return_str


def show_notes(sid, ldb):
    if int(dbAccess.get_element(sid, dbAccess.sid, dbAccess.sid, ldb)) < 0:
        return f'[r8udbBot: INDEX ERROR] SID "{sid}" not found'
    return_string = dbAccess.get_element(sid, dbAccess.sid, dbAccess.notes, ldb)
    if return_string == '':
        return_string = '<none>'
    return return_string


def show_pass(discord_id, ldb):
    if int(dbAccess.get_element(discord_id, dbAccess.discord_id, dbAccess.sid, ldb)) < 0:
        return f'[r8udbBot: INDEX ERROR] ID "{discord_id}" not found'
    if dbAccess.get_element(discord_id, dbAccess.discord_id, dbAccess.banned, ldb) == 'True':
        return f'You are currently banned'  # Don't let banned users see their password
    result = dbAccess.get_element(discord_id, dbAccess.discord_id, dbAccess.password, ldb)
    return result


def show_user(sid, ldb):
    if int(dbAccess.get_element(sid, dbAccess.sid, dbAccess.sid, ldb)) < 0:
        return f'[r8udbBot: INDEX ERROR] SID "{sid}" not found'
    result = ''
    for field_name in dbAccess.db_field_list:
        result += f'{field_name}: {dbAccess.get_element(sid, dbAccess.sid, field_name, ldb)}\n'
    return result


def new_pass(discord_id, ldb):
    if int(dbAccess.get_element(discord_id, dbAccess.discord_id, dbAccess.sid, ldb)) < 0:
        return f'[r8udbBot: INDEX ERROR] User "{discord_id}" not found'
    if dbAccess.get_element(discord_id, dbAccess.discord_id, dbAccess.banned, ldb) == 'True':
        return f'You are currently banned'  # Don't let banned users see their password
    new_pw = generate_password(random.randint(15, 25))
    dbAccess.set_element(discord_id,dbAccess.discord_id, dbAccess.password, new_pw, ldb)
    dbAccess.save_db(DB_FILENAME, ldb)
    return f'new password = {new_pw}'



if __name__ == '__main__':
    localDb = dbAccess.load_db(DB_FILENAME)
    print(check_ban_status(38, localDb))
