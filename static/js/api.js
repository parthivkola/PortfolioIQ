/**
 * API client. All backend calls go through here.
 */
const API_BASE = '/api/v1';

const api = {
  _token: localStorage.getItem('access_token'),
  _refresh: localStorage.getItem('refresh_token'),

  setTokens(access, refresh) {
    this._token = access;
    this._refresh = refresh;
    localStorage.setItem('access_token', access);
    localStorage.setItem('refresh_token', refresh);
  },

  clearTokens() {
    this._token = null;
    this._refresh = null;
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
  },

  isLoggedIn() { return !!this._token; },

  async request(method, path, body = null) {
    const headers = { 'Content-Type': 'application/json' };
    if (this._token) headers['Authorization'] = `Bearer ${this._token}`;
    const opts = { method, headers };
    if (body) opts.body = JSON.stringify(body);

    let res = await fetch(`${API_BASE}${path}`, opts);
    if (res.status === 401 && this._refresh) {
      const ok = await this._tryRefresh();
      if (ok) {
        opts.headers['Authorization'] = `Bearer ${this._token}`;
        res = await fetch(`${API_BASE}${path}`, opts);
      }
    }
    if (res.status === 204) return null;
    const data = await res.json();
    if (!res.ok) throw { status: res.status, ...data };
    return data;
  },

  async _tryRefresh() {
    try {
      const res = await fetch(`${API_BASE}/auth/refresh`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: this._refresh }),
      });
      if (res.ok) {
        const d = await res.json();
        this.setTokens(d.access_token, d.refresh_token);
        return true;
      }
    } catch (_) {}
    this.clearTokens();
    return false;
  },

  register(email, password, fullName) {
    return this.request('POST', '/auth/register', { email, password, full_name: fullName });
  },
  login(email, password) {
    return this.request('POST', '/auth/login', { email, password });
  },
  listPortfolios() { return this.request('GET', '/portfolio'); },
  createPortfolio(name) { return this.request('POST', '/portfolio', { name }); },
  deletePortfolio(id) { return this.request('DELETE', `/portfolio/${id}`); },
  listHoldings(pid) { return this.request('GET', `/holdings?portfolio_id=${pid}`); },
  createHolding(pid, assetType, symbol) {
    return this.request('POST', '/holdings', { portfolio_id: pid, asset_type: assetType, symbol });
  },
  listTransactions(pid, page = 1) {
    return this.request('GET', `/transactions?portfolio_id=${pid}&page=${page}&limit=20`);
  },
  createTransaction(hid, type, qty, price, ts) {
    return this.request('POST', '/transactions', {
      holding_id: hid, transaction_type: type, quantity: qty, price, timestamp: ts,
    });
  },
  getDashboard(pid) {
    return this.request('GET', `/dashboard${pid ? '?portfolio_id=' + pid : ''}`);
  },
  getPerformance(pid) { return this.request('GET', `/analytics/performance?portfolio_id=${pid}`); },
  getAllocation(pid) { return this.request('GET', `/analytics/allocation?portfolio_id=${pid}`); },
  searchMarket(q) { return this.request('GET', `/market/search?q=${encodeURIComponent(q)}`); },
  getQuote(sym) { return this.request('GET', `/market/quote/${encodeURIComponent(sym)}`); },
};
