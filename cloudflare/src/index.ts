/**
 * Cloudflare Worker - Telegram Bot
 * Manhwa botni Cloudflare Workers'ga ko'chirish
 * KV Storage ishlatiladi ma'lumotlarni saqlash uchun
 */

// ============ CONFIG ============
let BOT_TOKEN = '';
let ADMIN_IDS = '7538793043';
let WEBHOOK_SECRET = 'manhwa_webhook_2025';

// ============ TYPES ============
interface User {
  id: number;
  username: string | null;
  first_name: string;
  last_name: string | null;
  is_banned: boolean;
  is_vip: boolean;
  vip_expire: string | null;
  created_at: string;
}

interface Anime {
  code: number;
  name: string;
  genre: string | null;
  studio: string | null;
  poster_file_id: string | null;
  type: string;
  user_added: number;
  is_main: boolean;
  created_at: string;
}

interface Episode {
  anime_code: number;
  season: number;
  episode: number;
  file_id: string;
  file_type: string;
  file_name: string | null;
}

interface Channel {
  id: number;
  channel_id: string;
  channel_username: string;
  channel_name: string;
  channel_type: string;
  channel_url: string;
  is_main: boolean;
}

interface UserState {
  state: string;
  data: Record<string, any>;
  updated_at: number;
}

// ============ DB HELPERS (KV) ============
declare const DB: KVNamespace;
declare const STATE: KVNamespace;

async function dbGet(key: string): Promise<any> {
  return await DB.get(key, 'json');
}

async function dbPut(key: string, value: any): Promise<void> {
  await DB.put(key, JSON.stringify(value));
}

async function dbDelete(key: string): Promise<void> {
  await DB.delete(key);
}

// ============ USER FUNCTIONS ============
async function getUser(userId: number): Promise<User | null> {
  return await dbGet(`user:${userId}`);
}

async function createUser(userId: number, username: string | null, first_name: string, last_name: string | null): Promise<void> {
  const user: User = {
    id: userId,
    username,
    first_name,
    last_name,
    is_banned: false,
    is_vip: false,
    vip_expire: null,
    created_at: new Date().toISOString()
  };
  await dbPut(`user:${userId}`, user);
  
  // Update user list for stats
  const list = (await dbGet('users:list') as number[]) || [];
  if (!list.includes(userId)) {
    list.push(userId);
    await dbPut('users:list', list);
  }
}

async function getAdmins(): Promise<number[]> {
  return ADMIN_IDS.split(',').map(id => parseInt(id.trim())).filter(id => !isNaN(id));
}

// ============ ANIME FUNCTIONS ============
async function addAnime(code: number, name: string, genre: string | null, studio: string | null, poster_file_id: string | null): Promise<void> {
  const anime: Anime = {
    code,
    name,
    genre,
    studio,
    poster_file_id,
    type: 'oddiy',
    user_added: 0,
    is_main: false,
    created_at: new Date().toISOString()
  };
  await dbPut(`anime:${code}`, anime);
  
  const list = (await dbGet('anime:list') as number[]) || [];
  if (!list.includes(code)) {
    list.push(code);
    await dbPut('anime:list', list);
  }
}

async function getAnime(code: number): Promise<Anime | null> {
  return await dbGet(`anime:${code}`);
}

async function getAllAnime(): Promise<Anime[]> {
  const list = (await dbGet('anime:list') as number[]) || [];
  const animes: Anime[] = [];
  for (const code of list) {
    const anime = await getAnime(code);
    if (anime) animes.push(anime);
  }
  return animes;
}

async function addEpisode(code: number, season: number, episode: number, file_id: string, file_type: string, file_name: string | null): Promise<void> {
  const ep: Episode = {
    anime_code: code,
    season,
    episode,
    file_id,
    file_type,
    file_name
  };
  await dbPut(`ep:${code}:${season}:${episode}`, ep);
  
  // Track episode count
  const epListKey = `eps:${code}:${season}`;
  const list = (await dbGet(epListKey) as number[]) || [];
  if (!list.includes(episode)) {
    list.push(episode);
    await dbPut(epListKey, list);
  }
}

async function getEpisodes(code: number, season: number = 1): Promise<Episode[]> {
  const list = (await dbGet(`eps:${code}:${season}`) as number[]) || [];
  const episodes: Episode[] = [];
  for (const epNum of list.sort((a, b) => a - b)) {
    const ep = await dbGet(`ep:${code}:${season}:${epNum}`);
    if (ep) episodes.push(ep);
  }
  return episodes;
}

async function getNextCode(): Promise<number> {
  const list = (await dbGet('anime:list') as number[]) || [];
  if (list.length === 0) return 1;
  return Math.max(...list) + 1;
}

// ============ CHANNEL FUNCTIONS ============
async function getChannels(): Promise<Channel[]> {
  const channels: Channel[] = [];
  const list = await dbGet('channels:list') as number[];
  if (!list) return channels;
  for (const id of list) {
    const ch = await dbGet(`channel:${id}`);
    if (ch) channels.push(ch);
  }
  return channels;
}

async function addChannel(channel_id: string, username: string, name: string, type: string, url: string = ''): Promise<void> {
  const list = (await dbGet('channels:list') as number[]) || [];
  const id = Date.now();
  const ch: Channel = { id, channel_id, channel_username: username, channel_name: name, channel_type: type, channel_url: url, is_main: false };
  list.push(id);
  await dbPut(`channel:${id}`, ch);
  await dbPut('channels:list', list);
}

async function deleteChannelById(chDbId: number): Promise<void> {
  const list = (await dbGet('channels:list') as number[]) || [];
  await dbPut('channels:list', list.filter(id => id !== chDbId));
  await dbDelete(`channel:${chDbId}`);
}

// ============ USER STATE ============
async function getState(userId: number): Promise<UserState | null> {
  return await STATE.get(`state:${userId}`, 'json');
}

async function setState(userId: number, state: string, data: Record<string, any> = {}): Promise<void> {
  await STATE.put(`state:${userId}`, JSON.stringify({ state, data, updated_at: Date.now() }));
}

async function clearState(userId: number): Promise<void> {
  await STATE.delete(`state:${userId}`);
}

// ============ TELEGRAM API ============
async function tgApi(method: string, params: Record<string, any>): Promise<any> {
  const url = `https://api.telegram.org/bot${BOT_TOKEN}/${method}`;
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params)
  });
  return await res.json();
}

async function sendMessage(chatId: number | string, text: string, replyMarkup?: any, parseMode: string = 'HTML'): Promise<void> {
  const params: any = { chat_id: chatId, text, parse_mode: parseMode };
  if (replyMarkup) params.reply_markup = replyMarkup;
  await tgApi('sendMessage', params);
}

async function sendPhoto(chatId: number | string, photo: string, caption?: string, replyMarkup?: any): Promise<void> {
  const params: any = { chat_id: chatId, photo, caption, parse_mode: 'HTML' };
  if (replyMarkup) params.reply_markup = replyMarkup;
  await tgApi('sendPhoto', params);
}

async function answerCallback(callbackQueryId: string, text?: string): Promise<void> {
  await tgApi('answerCallbackQuery', { callback_query_id: callbackQueryId, text });
}

// ============ KEYBOARDS ============
function mainMenu(): any {
  return {
    inline_keyboard: [
      [{ text: "📚 Manhwa Kutubxonasi", callback_data: "library:0" }],
      [{ text: "🔍 Qidirish", callback_data: "search" }],
      [{ text: "🆕 Yangi qo'shilganlar", callback_data: "new_animes" }],
      [{ text: "👤 Shaxsiy kabinet", callback_data: "cabinet" }],
      [{ text: "📊 Statistika", callback_data: "stats" }],
      [{ text: "📢 Kanal", url: "https://t.me/manhwa_gate" }]
    ]
  };
}

function adminMenu(): any {
  return {
    inline_keyboard: [
      [{ text: "📡 Kanal boshqaruvi", callback_data: "admin_channels" }],
      [{ text: "🎬 Manhwa yuklash", callback_data: "anime_upload" }],
      [{ text: "📊 To'liq statistika", callback_data: "admin_stats" }],
      [{ text: "🔙 Bosh menyu", callback_data: "main_menu" }]
    ]
  };
}

function backAdmin(): any {
  return { inline_keyboard: [[{ text: "◀️ Orqaga", callback_data: "admin_panel" }]] };
}

// ============ HANDLERS ============

async function handleStart(userId: number, from: any): Promise<void> {
  let user = await getUser(userId);
  if (!user) {
    await createUser(userId, from.username, from.first_name, from.last_name);
  }
  
  const channels = await getChannels();
  const reqChannels = channels.filter(ch => ch.channel_type !== 'url');
  
  if (reqChannels.length > 0) {
    let subbed = true;
    const kb = { inline_keyboard: [] as any };
    
    for (const ch of reqChannels) {
      try {
        const res = await tgApi('getChatMember', { chat_id: ch.channel_id, user_id: userId });
        const status = res?.result?.status;
        if (status !== 'member' && status !== 'administrator' && status !== 'creator') {
          subbed = false;
          kb.inline_keyboard.push([{ text: `➕ ${ch.channel_name}`, url: ch.channel_url || `https://t.me/${ch.channel_username}` }]);
        }
      } catch (e) { subbed = false; }
    }
    
    if (!subbed) {
      kb.inline_keyboard.push([{ text: "✅ Tekshirish", callback_data: "main_menu" }]);
      await sendMessage(userId, "<b>❗ Botdan foydalanish uchun quyidagi kanallarga a'zo bo'ling:</b>", kb);
      return;
    }
  }

  await sendMessage(userId, `<b>Salom, ${from.first_name}!</b>\n\nManhwa botga xush kelibsiz. Quyidagi menyudan foydalaning:`, mainMenu());
}

async function handleCallback(userId: number, callback: any): Promise<void> {
  const data = callback.data;
  const admins = await getAdmins();
  const isAdmin = admins.includes(userId);

  if (data === 'main_menu') {
    await handleStart(userId, callback.from);
  } else if (data.startsWith('library:')) {
    const page = parseInt(data.split(':')[1]);
    const animes = await getAllAnime();
    if (animes.length === 0) {
      await sendMessage(userId, "😔 Kutubxona hozircha bo'sh.", { inline_keyboard: [[{ text: "◀️ Orqaga", callback_data: "main_menu" }]] });
      return;
    }
    
    const pageSize = 10;
    const start = page * pageSize;
    const currentAnimes = animes.slice(start, start + pageSize);
    
    let text = "<b>📚 Manhwa Kutubxonasi:</b>\n\n";
    const kb = { inline_keyboard: [] as any };
    
    for (const anime of currentAnimes) {
      kb.inline_keyboard.push([{ text: anime.name, callback_data: `view:${anime.code}` }]);
    }
    
    const navRow = [];
    if (page > 0) navRow.push({ text: "⬅️ Oldingi", callback_data: `library:${page - 1}` });
    if (start + pageSize < animes.length) navRow.push({ text: "Keyingi ➡️", callback_data: `library:${page + 1}` });
    if (navRow.length > 0) kb.inline_keyboard.push(navRow);
    kb.inline_keyboard.push([{ text: "🏠 Menyu", callback_data: "main_menu" }]);
    
    await sendMessage(userId, text, kb);
  } else if (data.startsWith('view:')) {
    const code = parseInt(data.split(':')[1]);
    const anime = await getAnime(code);
    if (!anime) {
      await answerCallback(callback.id, "❌ Manhwa topilmadi.");
      return;
    }
    
    const episodes = await getEpisodes(code);
    let text = `<b>🎬 ${anime.name}</b>\n\n`;
    if (anime.genre) text += `🎭 Janr: ${anime.genre}\n`;
    if (anime.studio) text += `🎙 Studiya: ${anime.studio}\n`;
    text += `📦 Jami: ${episodes.length} bob.\n\n`;
    text += `Boblarni ko'rish uchun quyidagi tugmalarni bosing:`;
    
    const kb = { inline_keyboard: [] as any };
    // Group episodes in rows of 5
    for (let i = 0; i < episodes.length; i += 5) {
      const row = episodes.slice(i, i + 5).map(ep => ({
        text: `${ep.episode}`,
        callback_data: `get_ep:${code}:${ep.episode}`
      }));
      kb.inline_keyboard.push(row);
    }
    kb.inline_keyboard.push([{ text: "◀️ Kutubxonaga qaytish", callback_data: "library:0" }]);
    
    if (anime.poster_file_id) {
      await sendPhoto(userId, anime.poster_file_id, text, kb);
    } else {
      await sendMessage(userId, text, kb);
    }
  } else if (data.startsWith('get_ep:')) {
    const [_, code, epNum] = data.split(':').map(Number);
    const ep = await dbGet(`ep:${code}:1:${epNum}`);
    if (ep) {
      const method = ep.file_type === 'video' ? 'sendVideo' : 'sendDocument';
      await tgApi(method, {
        chat_id: userId,
        [ep.file_type]: ep.file_id,
        caption: `<b>📖 ${epNum}-bob</b>`
      });
    }
  } else if (data === 'search') {
    await setState(userId, 'searching');
    await sendMessage(userId, "🔍 Qidirish uchun manhwa nomini yoki kodini yuboring:", { inline_keyboard: [[{ text: "❌ Bekor qilish", callback_data: "main_menu" }]] });
  } else if (data === 'stats') {
    const users = (await dbGet('users:list') as number[]) || [];
    const animes = (await dbGet('anime:list') as number[]) || [];
    await sendMessage(userId, `<b>📊 Bot statistikasi:</b>\n\n👤 Foydalanuvchilar: ${users.length}\n🎬 Manhwalar: ${animes.length}`, { inline_keyboard: [[{ text: "🏠 Menyu", callback_data: "main_menu" }]] });
  } else if (data === 'cabinet') {
    const user = await getUser(userId);
    let text = `<b>👤 Shaxsiy kabinet:</b>\n\n`;
    text += `🆔 ID: <code>${userId}</code>\n`;
    text += `👤 Ism: ${user?.first_name || 'Noma\'lum'}\n`;
    text += `💎 VIP: ${user?.is_vip ? '✅' : '❌'}\n`;
    text += `📅 Ro'yxatdan o'tilgan: ${user?.created_at ? new Date(user.created_at).toLocaleDateString() : 'Noma\'lum'}`;
    await sendMessage(userId, text, { inline_keyboard: [[{ text: "🏠 Menyu", callback_data: "main_menu" }]] });
  } else if (data === 'new_animes') {
    const animes = await getAllAnime();
    const sorted = animes.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()).slice(0, 5);
    if (sorted.length === 0) {
      await sendMessage(userId, "🆕 Hozircha yangi manhwalar yo'q.", { inline_keyboard: [[{ text: "🏠 Menyu", callback_data: "main_menu" }]] });
    } else {
      let text = "<b>🆕 Oxirgi qo'shilgan manhwalar:</b>\n\n";
      const kb = { inline_keyboard: [] as any };
      for (const a of sorted) {
        kb.inline_keyboard.push([{ text: a.name, callback_data: `view:${a.code}` }]);
      }
      kb.inline_keyboard.push([{ text: "🏠 Menyu", callback_data: "main_menu" }]);
      await sendMessage(userId, text, kb);
    }
  } else if (data === 'admin_panel' && isAdmin) {
    await sendMessage(userId, "<b>🔧 Admin paneli:</b>", adminMenu());
  } else if (data === 'anime_upload' && isAdmin) {
    const nextCode = await getNextCode();
    await setState(userId, 'waiting_name', { code: nextCode });
    await sendMessage(userId, `🔢 Auto kod: <b>${nextCode}</b>\n\n📝 Manhwa nomini kiriting:`, { inline_keyboard: [[{ text: "❌ Bekor qilish", callback_data: "admin_panel" }]] });
  } else if (data === 'admin_channels' && isAdmin) {
    const channels = await getChannels();
    let text = "<b>📡 Kanallar ro'yxati:</b>\n\n";
    const kb = { inline_keyboard: [] as any };
    for (const ch of channels) {
      text += `• ${ch.channel_name} (${ch.channel_type})\n`;
      kb.inline_keyboard.push([{ text: `🗑 ${ch.channel_name}`, callback_data: `del_ch:${ch.id}` }]);
    }
    kb.inline_keyboard.push([{ text: "➕ Kanal qo'shish", callback_data: "add_ch" }]);
    kb.inline_keyboard.push([{ text: "◀️ Orqaga", callback_data: "admin_panel" }]);
    await sendMessage(userId, text, kb);
  } else if (data === 'add_ch' && isAdmin) {
    await setState(userId, 'waiting_ch_id');
    await sendMessage(userId, "🆔 Kanal ID sini yuboring (masalan: -100...):", { inline_keyboard: [[{ text: "❌ Bekor qilish", callback_data: "admin_channels" }]] });
  } else if (data.startsWith('del_ch:') && isAdmin) {
    const id = parseInt(data.split(':')[1]);
    await deleteChannelById(id);
    await answerCallback(callback.id, "✅ Kanal o'chirildi.");
    await handleCallback(userId, { data: 'admin_channels', from: callback.from });
  }

  await answerCallback(callback.id);
}

async function handleMessage(userId: number, message: any): Promise<void> {
  const text = message.text;
  const state = await getState(userId);
  const admins = await getAdmins();
  const isAdmin = admins.includes(userId);

  if (text === '/start') {
    await handleStart(userId, message.from);
    return;
  }

  if (text === '/admin' && isAdmin) {
    await sendMessage(userId, "<b>🔧 Admin paneli:</b>", adminMenu());
    return;
  }

  if (state) {
    if (state.state === 'searching') {
      const query = text.toLowerCase();
      const animes = await getAllAnime();
      const results = animes.filter(a => a.name.toLowerCase().includes(query) || a.code.toString() === query);
      
      if (results.length === 0) {
        await sendMessage(userId, "❌ Hech narsa topilmadi. Qayta urinib ko'ring:");
      } else {
        await clearState(userId);
        let resp = `<b>🔍 Qidiruv natijalari:</b>\n\n`;
        const kb = { inline_keyboard: [] as any };
        for (const a of results.slice(0, 10)) {
          kb.inline_keyboard.push([{ text: a.name, callback_data: `view:${a.code}` }]);
        }
        await sendMessage(userId, resp, kb);
      }
    } else if (isAdmin) {
      const data = state.data;
      if (state.state === 'waiting_name') {
        data.name = text;
        await setState(userId, 'waiting_genre', data);
        await sendMessage(userId, "🎭 Manhwa janrini kiriting (yoki /skip):");
      } else if (state.state === 'waiting_genre') {
        data.genre = text === '/skip' ? null : text;
        await setState(userId, 'waiting_studio', data);
        await sendMessage(userId, "🎙 Studiya nomini kiriting (yoki /skip):");
      } else if (state.state === 'waiting_studio') {
        data.studio = text === '/skip' ? null : text;
        await setState(userId, 'waiting_poster', data);
        await sendMessage(userId, "🎬 Posterni yuboring (Rasm):");
      } else if (state.state === 'waiting_poster' && message.photo) {
        data.poster = message.photo[message.photo.length - 1].file_id;
        await addAnime(data.code, data.name, data.genre, data.studio, data.poster);
        await setState(userId, 'waiting_eps', { code: data.code, count: 0 });
        await sendMessage(userId, "✅ Manhwa yaratildi! Endi boblarni (Video/Fayl) ketma-ket yuboring. Tugatgach /done deb yozing.");
      } else if (state.state === 'waiting_eps') {
        if (text === '/done') {
          await clearState(userId);
          await sendMessage(userId, "✅ Barcha boblar saqlandi!", backAdmin());
        } else if (message.video || message.document) {
          const file = message.video || message.document;
          data.count++;
          await addEpisode(data.code, 1, data.count, file.file_id, message.video ? 'video' : 'document', file.file_name || null);
          // Silent ack
        }
      } else if (state.state === 'waiting_ch_id') {
        data.ch_id = text;
        await setState(userId, 'waiting_ch_name', data);
        await sendMessage(userId, "📝 Kanal nomini kiriting:");
      } else if (state.state === 'waiting_ch_name') {
        data.ch_name = text;
        await setState(userId, 'waiting_ch_user', data);
        await sendMessage(userId, "🔗 Kanal username-ini kiriting (masalan: manhwa_gate):");
      } else if (state.state === 'waiting_ch_user') {
        await addChannel(data.ch_id, text, data.ch_name, 'public');
        await clearState(userId);
        await sendMessage(userId, "✅ Kanal qo'shildi!", backAdmin());
      }
    }
  } else if (!isNaN(text)) {
    // Direct code entry
    const anime = await getAnime(parseInt(text));
    if (anime) {
      await handleCallback(userId, { data: `view:${anime.code}`, from: message.from });
    }
  }
}

export default {
  async fetch(request: Request, env: any): Promise<Response> {
    (globalThis as any).__env__ = env;
    (globalThis as any).DB = env.DB;
    (globalThis as any).STATE = env.STATE;

    BOT_TOKEN = env.BOT_TOKEN || '';
    ADMIN_IDS = env.ADMIN_IDS || '7538793043';
    WEBHOOK_SECRET = env.WEBHOOK_SECRET || 'manhwa_webhook_2025';

    const url = new URL(request.url);
    console.log(`Incoming request: ${url.pathname}`);
    if (url.pathname === `/webhook/${WEBHOOK_SECRET}` && request.method === 'POST') {
      try {
        const update = await request.json() as any;
        console.log(`Update received: ${JSON.stringify(update)}`);
        if (update.message) {
          console.log(`Handling message from ${update.message.from.id}`);
          await handleMessage(update.message.from.id, update.message);
        }
        else if (update.callback_query) await handleCallback(update.callback_query.from.id, update.callback_query);
        return new Response('OK');
      } catch (e) { 
        console.error(e);
        return new Response('Error', { status: 500 }); 
      }
    }
    return new Response('Not Found', { status: 404 });
  }
};
