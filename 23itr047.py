import sqlite3
import tkinter as tk
from tkinter import messagebox

conn = sqlite3.connect('voting_system.db')
c = conn.cursor()

c.execute('''CREATE TABLE IF NOT EXISTS voters (
        card_no INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        password TEXT NOT NULL,
        validated BOOLEAN NOT NULL DEFAULT FALSE
    )
''')
c.execute('''CREATE TABLE IF NOT EXISTS admins (
        username TEXT PRIMARY KEY,
        password TEXT NOT NULL
    )
''')
c.execute('''CREATE TABLE IF NOT EXISTS candidates (
        name TEXT PRIMARY KEY,
        votes INTEGER NOT NULL DEFAULT 0
    )
''')
c.execute('''CREATE TABLE IF NOT EXISTS places (
        name TEXT PRIMARY KEY
    )
''')

c.execute('DROP TABLE IF EXISTS votes')
c.execute('''CREATE TABLE votes (
        card_no INTEGER,
        candidate TEXT,
        place TEXT,
        FOREIGN KEY(card_no) REFERENCES voters(card_no),
        FOREIGN KEY(candidate) REFERENCES candidates(name),
        FOREIGN KEY(place) REFERENCES places(name)
    )
''')

conn.commit()


def admin_login(username, password):
    c.execute("SELECT password FROM admins WHERE username = ?", (username,))
    result = c.fetchone()
    return result and password == result[0]


def add_admin(username, password):
    try:
        c.execute("INSERT INTO admins (username, password) VALUES (?, ?)", (username, password))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False


def add_citizen(card_no, name, password):
    try:
        c.execute("INSERT INTO voters (card_no, name, password) VALUES (?, ?, ?)", (card_no, name, password))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False


def add_candidate(name):
    try:
        c.execute("INSERT INTO candidates (name) VALUES (?)", (name,))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False


def add_place(name):
    try:
        c.execute("INSERT INTO places (name) VALUES (?)", (name,))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False


def generate_report():
    c.execute("SELECT name, votes FROM candidates")
    results = c.fetchall()
    return results


def generate_place_report():
    """Generates a report showing the count of votes cast from each place."""
    c.execute("SELECT place, COUNT(*) FROM votes GROUP BY place")
    results = c.fetchall()
    if results:
        report_message = "\n".join(f"{place}: {count} votes" for place, count in results)
    else:
        report_message = "No votes cast yet."
    messagebox.showinfo("Place Report", report_message)


def reset_votes():
    c.execute("UPDATE candidates SET votes = 0")
    c.execute("DELETE FROM votes")
    conn.commit()


def voter_login(card_no, password):
    c.execute("SELECT password, validated FROM voters WHERE card_no = ?", (card_no,))
    result = c.fetchone()
    if result and password == result[0]:
        if not result[1]:
            return True, "Login successful and voter is validated."
        else:
            return False, "Voter has already voted."
    return False, "Invalid credentials or voter not found."


def cast_vote(card_no, candidate, place):
    c.execute("INSERT INTO votes (card_no, candidate, place) VALUES (?, ?, ?)", (card_no, candidate, place))
    c.execute("UPDATE voters SET validated = TRUE WHERE card_no = ?", (card_no,))
    c.execute("UPDATE candidates SET votes = votes + 1 WHERE name = ?", (candidate,))
    conn.commit()
    return True


def clear_database():
    """Clears all data from the database."""
    try:
        c.execute("DELETE FROM votes")
        c.execute("DELETE FROM candidates")
        c.execute("DELETE FROM voters")
        c.execute("DELETE FROM admins")
        c.execute("DELETE FROM places")
        conn.commit()
        print("Database cleared successfully.")
        return True
    except Exception as e:
        print(f"An error occurred while clearing the database: {e}")
        return False


def clear_database_gui():
    if messagebox.askyesno("Confirm Clear",
                           "Are you sure you want to clear the database? This action cannot be undone."):
        if clear_database():
            messagebox.showinfo("Success", "Database cleared successfully.")
        else:
            messagebox.showerror("Error", "Failed to clear the database.")


def admin_menu():
    admin_window = tk.Toplevel()
    admin_window.title("Admin Menu")
    admin_window.geometry("600x400")

    def add_citizen_cmd():
        card_no = int(card_no_entry.get())
        name = name_entry.get()
        password = password_entry.get()
        if add_citizen(card_no, name, password):
            messagebox.showinfo("Success", f"Citizen {name} added successfully.")
        else:
            messagebox.showerror("Error", "Citizen already exists or invalid data.")

    def add_candidate_cmd():
        candidate_name = candidate_entry.get()
        if add_candidate(candidate_name):
            messagebox.showinfo("Success", f"Candidate {candidate_name} added successfully.")
        else:
            messagebox.showerror("Error", "Candidate already exists or invalid data.")

    def add_place_cmd():
        place_name = place_entry.get()
        if add_place(place_name):
            messagebox.showinfo("Success", f"Place {place_name} added successfully.")
        else:
            messagebox.showerror("Error", "Place already exists or invalid data.")

    def generate_report_cmd():
        report = generate_report()
        report_message = "\n".join(f"{candidate}: {votes} votes" for candidate, votes in report)
        messagebox.showinfo("Election Report", report_message)

    card_no_entry = tk.Entry(admin_window)
    name_entry = tk.Entry(admin_window)
    password_entry = tk.Entry(admin_window, show='*')
    candidate_entry = tk.Entry(admin_window)
    place_entry = tk.Entry(admin_window)

    tk.Label(admin_window, text="Card No:").pack()
    card_no_entry.pack()
    tk.Label(admin_window, text="Name:").pack()
    name_entry.pack()
    tk.Label(admin_window, text="Password:").pack()
    password_entry.pack()
    tk.Button(admin_window, text="Add Citizen", command=add_citizen_cmd).pack()

    tk.Label(admin_window, text="Candidate Name:").pack()
    candidate_entry.pack()
    tk.Button(admin_window, text="Add Candidate", command=add_candidate_cmd).pack()

    tk.Label(admin_window, text="Place Name:").pack()
    place_entry.pack()
    tk.Button(admin_window, text="Add Place", command=add_place_cmd).pack()

    tk.Button(admin_window, text="Generate Report", command=generate_report_cmd).pack()
    tk.Button(admin_window, text="Place Report", command=generate_place_report).pack(
        pady=10) 

    tk.Button(admin_window, text="Reset Votes", command=reset_votes).pack(pady=10)
    tk.Button(admin_window, text="Clear Database", command=clear_database_gui).pack(pady=10)


def voter_menu():
    voter_window = tk.Toplevel()
    voter_window.title("Voter Menu")
    voter_window.geometry("600x400")

    def cast_vote_cmd():
        card_no = int(card_no_entry.get())
        password = password_entry.get()
        candidate_name = candidate_var.get()
        place_name = place_var.get()
        success, message = voter_login(card_no, password)

        if success:
            if cast_vote(card_no, candidate_name, place_name):
                messagebox.showinfo("Success", "Vote cast successfully!")
            else:
                messagebox.showerror("Error", "Failed to cast vote.")
        else:
            messagebox.showerror("Error", message)

    def populate_candidates_and_places():
        c.execute("SELECT name FROM candidates")
        candidates = [row[0] for row in c.fetchall()]
        if candidates:
            candidate_var.set(candidates[0])
            candidate_menu['menu'].delete(0, 'end')
            for candidate in candidates:
                candidate_menu['menu'].add_command(label=candidate, command=tk._setit(candidate_var, candidate))

        c.execute("SELECT name FROM places")
        places = [row[0] for row in c.fetchall()]
        if places:
            place_var.set(places[0])
            place_menu['menu'].delete(0, 'end')
            for place in places:
                place_menu['menu'].add_command(label=place, command=tk._setit(place_var, place))

    card_no_entry = tk.Entry(voter_window)
    password_entry = tk.Entry(voter_window, show='*')
    candidate_var = tk.StringVar(voter_window)
    place_var = tk.StringVar(voter_window)

    candidate_var.set("Select Candidate")
    candidate_menu = tk.OptionMenu(voter_window, candidate_var, "")
    place_var.set("Select Place")
    place_menu = tk.OptionMenu(voter_window, place_var, "")

    populate_candidates_and_places()

    tk.Label(voter_window, text="Card No:").pack()
    card_no_entry.pack()
    tk.Label(voter_window, text="Password:").pack()
    password_entry.pack()
    tk.Label(voter_window, text="Candidate:").pack()
    candidate_menu.pack()
    tk.Label(voter_window, text="Place:").pack()
    place_menu.pack()
    tk.Button(voter_window, text="Cast Vote", command=cast_vote_cmd).pack(pady=10)


def main_menu():
    main_window = tk.Tk()
    main_window.title("Voting System")
    main_window.geometry("600x400")

    def admin_login_cmd():
        username = username_entry.get()
        password = password_entry.get()
        if admin_login(username, password):
            admin_menu()
        else:
            messagebox.showerror("Error", "Admin login failed.")

    def open_voter_menu():
        voter_menu()

    username_entry = tk.Entry(main_window)
    password_entry = tk.Entry(main_window, show='*')

    tk.Label(main_window, text="Admin Username:").pack()
    username_entry.pack()
    tk.Label(main_window, text="Admin Password:").pack()
    password_entry.pack()
    tk.Button(main_window, text="Admin Login", command=admin_login_cmd).pack()
    tk.Button(main_window, text="Voter Menu", command=open_voter_menu).pack()

    main_window.mainloop()


if __name__ == "_main_":
    if add_admin("admin", "password"):
        print("Admin added successfully.")

    main_menu()