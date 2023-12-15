# ASSIGNMENT 1: Simple File-Sharing System
## How to run
#### Server:
1. On the server host, run `main_server.py`.
2. Enter port, for example `12000`.
3. Test with following commands (after running at least one client):
    - List all files in `username`'s repo: `discover username`
    - Live check the client named `username` for `n` times consecutively: `ping username (n)`
    - List all registered hosts and their information: `show`

#### Client:
1. On the client host, run `main_client.py`.
2. Connect to the server using IP address and listening port, for example `connect 26.152.222.248 12001`.
3. Register / Log in (if registered), for example `register dat 123` / `login dat 123`.
4. Test with following commands (recently `lname` and `fname` isn't allowed to have space):
    - Publish local file at `lname` to the client's repo as `fname`: `publish lname fname`
    - Fetch a copy of the file named `fname` from any connected client to the current client's repo as `rname` if provided, otherwise `fname`: `fetch fname (rname)`.
    - Delete a file named `fname` in the client's repo: `delete fname`.
    - Search a file named `fname` to check if it is available in any connected client with the same server: `search fname`.
    - View all files in the client's repo: `view`.
5. More advanced actions:
    - Change password of the current account, for example `change_password 123 456`.
    - Log out the current account and be offline: `logout`.
    - Disconnect with the current server: `disconnect`.
