const Api = {
  async get(path) {
    const res = await fetch(path);
    if (!res.ok) throw new Error(`GET ${path} failed (${res.status})`);
    return res.json();
  },

  async postJSON(path, body) {
    const res = await fetch(path, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    let data;
    try {
      data = await res.json();
    } catch (e) {
      throw new Error(`Server returned HTTP ${res.status}`);
    }
    if (!res.ok) throw new Error(data.error || `POST ${path} failed (${res.status})`);
    return data;
  },
};
