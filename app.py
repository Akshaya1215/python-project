import gradio as gr
from pymongo import MongoClient

# MongoDB Connection
client = MongoClient("mongodb://localhost:27017/")
db = client["library_db"]
users_col = db["users"]
books_col = db["books"]

# Add User
def add_user(user_id, name):
    if users_col.find_one({"user_id": user_id}):
        return f"❌ User with ID {user_id} already exists."
    users_col.insert_one({
        "user_id": user_id,
        "name": name,
        "borrowed_books": []
    })
    return f"✅ User {name} added successfully."

# Add Book
def add_book(book_id, title, author, quantity):
    if books_col.find_one({"book_id": book_id}):
        return f"❌ Book with ID {book_id} already exists."
    books_col.insert_one({
        "book_id": book_id,
        "title": title,
        "author": author,
        "quantity": quantity,
        "available": quantity
    })
    return f"✅ {quantity} copies of '{title}' added successfully."

# Issue Book
def issue_book(user_id, book_id):
    user = users_col.find_one({"user_id": user_id})
    book = books_col.find_one({"book_id": book_id})

    if not user:
        return "❌ User not found."
    if not book:
        return "❌ Book not found."
    if book["available"] < 1:
        return "❌ No available copies of the book."

    users_col.update_one({"user_id": user_id}, {"$push": {"borrowed_books": book_id}})
    books_col.update_one({"book_id": book_id}, {"$inc": {"available": -1}})

    return f"📚 Book '{book['title']}' issued to {user['name']}."

# Return Book
def return_book(user_id, book_id):
    user = users_col.find_one({"user_id": user_id})
    book = books_col.find_one({"book_id": book_id})

    if not user:
        return "❌ User not found."
    if not book:
        return "❌ Book not found."
    if book_id not in user.get("borrowed_books", []):
        return "❌ This book is not issued to the user."

    users_col.update_one({"user_id": user_id}, {"$pull": {"borrowed_books": book_id}})
    books_col.update_one({"book_id": book_id}, {"$inc": {"available": 1}})

    return f"📥 Book '{book['title']}' returned by {user['name']}."

# Delete User
def delete_user(user_id):
    user = users_col.find_one({"user_id": user_id})
    if not user:
        return f"❌ User with ID {user_id} not found."
    if user["borrowed_books"]:
        return f"❌ Cannot delete user with borrowed books: {user['borrowed_books']}"
    users_col.delete_one({"user_id": user_id})
    return f"🗑️ User {user_id} deleted successfully."

# Delete Book
def delete_book(book_id):
    book = books_col.find_one({"book_id": book_id})
    if not book:
        return f"❌ Book with ID {book_id} not found."
    if book["available"] < book["quantity"]:
        return f"❌ Cannot delete book '{book['title']}' because some copies are still issued."
    books_col.delete_one({"book_id": book_id})
    return f"🗑️ Book {book_id} deleted successfully."

# View All Data
def view_data():
    try:
        users = list(users_col.find())
        books = list(books_col.find())

        user_lines = []
        for u in users:
            user_id = u.get("user_id", "N/A")
            name = u.get("name", "N/A")
            borrowed = u.get("borrowed_books", [])
            user_lines.append(f"{user_id}: {name} - Borrowed: {borrowed}")

        book_lines = []
        for b in books:
            book_id = b.get("book_id", "N/A")
            title = b.get("title", "N/A")
            author = b.get("author", "N/A")
            available = b.get("available", 0)
            quantity = b.get("quantity", 0)
            book_lines.append(f"{book_id}: {title} by {author} - Available: {available}/{quantity}")

        return "📘 USERS:\n" + "\n".join(user_lines) + "\n\n📚 BOOKS:\n" + "\n".join(book_lines)

    except Exception as e:
        return f"❌ Error fetching data: {e}"

# Gradio UI
with gr.Blocks() as demo:
    gr.Markdown("# 📚 EduLibrary Hub")

    with gr.Tab("Add User"):
        uid = gr.Text(label="User ID")
        uname = gr.Text(label="Name")
        user_output = gr.Textbox(label="Output")
        user_btn = gr.Button("Add User")
        user_btn.click(fn=add_user, inputs=[uid, uname], outputs=user_output)

    with gr.Tab("Add Book"):
        bid = gr.Text(label="Book ID")
        btitle = gr.Text(label="Title")
        bauthor = gr.Text(label="Author")
        bqty = gr.Number(label="Quantity", value=1, precision=0)
        book_output = gr.Textbox(label="Output")
        book_btn = gr.Button("Add Book")
        book_btn.click(fn=add_book, inputs=[bid, btitle, bauthor, bqty], outputs=book_output)

    with gr.Tab("Issue Book"):
        issue_uid = gr.Text(label="User ID")
        issue_bid = gr.Text(label="Book ID")
        issue_output = gr.Textbox(label="Output")
        issue_btn = gr.Button("Issue Book")
        issue_btn.click(fn=issue_book, inputs=[issue_uid, issue_bid], outputs=issue_output)

    with gr.Tab("Return Book"):
        return_uid = gr.Text(label="User ID")
        return_bid = gr.Text(label="Book ID")
        return_output = gr.Textbox(label="Output")
        return_btn = gr.Button("Return Book")
        return_btn.click(fn=return_book, inputs=[return_uid, return_bid], outputs=return_output)

    with gr.Tab("Delete User"):
        del_uid = gr.Text(label="User ID to Delete")
        del_user_output = gr.Textbox(label="Output")
        del_user_btn = gr.Button("Delete User")
        del_user_btn.click(fn=delete_user, inputs=del_uid, outputs=del_user_output)

    with gr.Tab("Delete Book"):
        del_bid = gr.Text(label="Book ID to Delete")
        del_book_output = gr.Textbox(label="Output")
        del_book_btn = gr.Button("Delete Book")
        del_book_btn.click(fn=delete_book, inputs=del_bid, outputs=del_book_output)

    with gr.Tab("View Data"):
        data_output = gr.Textbox(label="All Users and Books", lines=25, max_lines=40)
        data_btn = gr.Button("Refresh Data")
        data_btn.click(fn=view_data, outputs=data_output)

# Launch the app
demo.launch()
