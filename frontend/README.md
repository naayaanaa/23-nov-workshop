# Campus Connect frontend

Static frontend for the Flask API in `../backend/app.py`.

1. Configure the backend's Supabase environment variables and run it on port 5000.
2. Set `CAMPUS_CONNECT_API` in `config.js` to the backend URL if it is not `http://localhost:5000`.
3. Serve this folder with any static web server and open `index.html` through that server.
4. Use the profile button to save your user UUID before registering or viewing your registrations.

The organizer portal asks for the organizer UUID and an event, then uses the API's organizer ownership check. UUIDs are stored only in this browser's local storage.

Use the **View** selector to switch between Student and Organizer views. Student view is the default and hides the organizer attendee list. This view selector changes the interface; it is not an authentication boundary.
