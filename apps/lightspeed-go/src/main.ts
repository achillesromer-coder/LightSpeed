import "./styles.css";

const app = document.getElementById("app");
if (!app) throw new Error("LightSpeed Go mount node #app not found.");

app.innerHTML = `
  <main class="lsgo-login">
    <section class="lsgo-card">
      <p class="kicker">LightSpeed Go</p>
      <h1>Römer Industries Operations</h1>
      <p>Mobile-first operations shell. Projects are permission-filtered. Workspaces appear only when enabled.</p>
      <form>
        <label>Username / Email <input placeholder="username / email" autocomplete="username" /></label>
        <label>Password <input placeholder="password" type="password" minlength="4" maxlength="16" autocomplete="current-password" /></label>
        <button type="button">Sign in</button>
      </form>
    </section>
  </main>
`;
