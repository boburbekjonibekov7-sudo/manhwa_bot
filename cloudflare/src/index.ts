/**
 * Cloudflare Worker - Telegram Bot
 * Manhwa botni Cloudflare Workers'ga ko'chirish
 * KV Storage ishlatiladi ma'lumotlarni saqlash uchun
 */

// ============ CONFIG ============
const BOT_TOKEN = (typeof __env__ !== 'undefined' && __env__.BOT_TOKEN) || '';
const ADMIN_IDS = (typeof __env__ !== 'undefined' && __env__.ADMIN_IDS) || '7538793043';
const WEBHOOK_SECRET = (typeof __env__ !== 'undefined' && __env__.WEBHOOK_SECRET) || 'manhwa_webhook_2025';

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

interface Settings {
  [key: string]: string;
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
  const val = await DB.get(key, 'json');
  return val;
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
}

async function getAnime(code: number): Promise<Anime | null> {
  return await dbGet(`anime:${code}`);
}

async function getEpisodes(code: number, season: number = 1): Promise<Episode[]> {
  const episodes: Episode[] = [];
  let i = 1;
  while (true) {
    const ep = await dbGet(`ep:${code}:${season}:${i}`);
    if (!ep) break;
    episodes.push(ep);
    i++;
  }
  return episodes;
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
}

async function getNextCode(): Promise<number> {
  for (let i = 1; i <= 999; i++) {
    const anime = await getAnime(i);
    if (!anime) {
      return i;
    }
  }
  return 1000;
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
  const id = list.length + 1;
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

// ============ SETTINGS ============
async function getSetting(key: string): Promise<string | null> {
  return await DB.get(`setting:${key}`, 'text');
}

async function setSetting(key: string, value: string): Promise<void> {
  await DB.put(`setting:${key}`, value);
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

async function sendMessage(chatId: number | string, text: string, replyMarkup?: any, parseMode?: string): Promise<void> {
  const params: any = { chat_id: chatId, text, parse_mode: parseMode || undefined };
  if (replyMarkup) params.reply_markup = replyMarkup;
  await tgApi('sendMessage', params);
}

async function sendPhoto(chatId: number | string, photo: string, caption?: string, replyMarkup?: any): Promise<void> {
  const params: any = { chat_id: chatId, photo, parse_mode: undefined as any };
  if (caption) params.caption = caption;
  if (replyMarkup) params.reply_markup = replyMarkup;
  await tgApi('sendPhoto', params);
}

// ============ KEYBOARDS ============
function mainMenu(): any {
  return {
    inline_keyboard: [
      [{ text: "📚 Manhwa Kutubxonasi", callback_data: "library" }],
      [{ text: "🔍 Qidirish", callback_data: "search" }],
      [{ text: "🆕 Yangi qo'shilganlar", callback_data: "new_animes" }],
      [{ text: "👤 Shaxsiy kabinet", callback_data: "cabinet" }],
      [{ text: "📞 Bog'lanish", callback_data: "contact" }],
      [{ text: "📢 Kanal", callback_data: "channel" }]
    ]
  };
}

function backMenu(): any {
  return {
    inline_keyboard: [
      [{ text: "◀️ Orqaga", callback_data: "main_menu" }]
    ]
  };
}

function cancelAdmin(): any {
  return {
    inline_keyboard: [
      [{ text: "❌ Bekor qilish", callback_data: "cancel_admin" }]
    ]
  };
}

function backAdmin(backCb: string = "main_menu"): any {
  return {
    inline_keyboard: [
      [{ text: "◀️ Orqaga", callback_data: backCb }]
    ]
  };
}

function adminMenu(): any {
  return {
    inline_keyboard: [
      [{ text: "📡 Kanal boshqaruvi", callback_data: "admin_channels" }],
      [{ text: "🎬 Manhwa yuklash", callback_data: "anime_upload" }],
      [{ text: "📊 Statistika", callback_data: "admin_stats" }],
      [{ text: "⚙️ Sozlamalar", callback_data: "admin_settings" }],
      [{ text: "🔙 Bosh menyu", callback_data: "main_menu" }]
    ]
  };
}

function skipKb(skipData: string): any {
  return {
    inline_keyboard: [
      [{ text: "⏭ Skip", callback_data: skipData }]
    ]
  };
}

function channelsMenu(): any {
  return {
    inline_keyboard: [
      [{ text: "🔐 Majburiy obuna kanallar", callback_data: "ch_required" }],
      [{ text: "📢 Asosiy kanallar (post uchun)", callback_data: "ch_main" }],
      [{ text: "🔙 Orqaga", callback_data: "admin_panel" }]
    ]
  };
}

function requiredChannels(): any {
  return {
    inline_keyboard: [
      [{ text: "➕ Kanal qo'shish", callback_data: "ch_add" }],
      [{ text: "📋 Ro'yxatni ko'rish", callback_data: "ch_list" }],
      [{ text: "🗑 Kanalni o'chirish", callback_data: "ch_delete" }],
      [{ text: "🌐 Oddiy havola kanallar", callback_data: "ch_url" }],
      [{ text: "🔙 Kanal boshqaruvi", callback_data: "admin_channels" }]
    ]
  };
}

function urlChannels(): any {
  return {
    inline_keyboard: [
      [{ text: "➕ Oddiy havola qo'shish", callback_data: "url_ch_add" }],
      [{ text: "📋 Ro'yxatni ko'rish", callback_data: "url_ch_list" }],
      [{ text: "🔙 Kanal boshqaruvi", callback_data: "admin_channels" }]
    ]
  };
}

function channelTypeKb(): any {
  return {
    inline_keyboard: [
      [{ text: "📢 Ommaviy / Shaxsiy", callback_data: "ch_type:public" }],
      [{ text: "🔐 Shaxsiy / So'rovli", callback_data: "ch_type:private_link" }],
      [{ text: "🌐 Oddiy havola", callback_data: "ch_type:url" }],
      [{ text: "◀️ Orqaga", callback_data: "ch_required" }]
    ]
  };
}

// ============ HANDLERS ============

async function handleStart(userId: number, username: string | null, firstName: string, lastName: string | null): Promise<void> {
  let user = await getUser(userId);
  if (!user) {
    await createUser(userId, username, firstName, lastName);
    await sendMessage(userId, "👋 Assalomu alaykum! Manhwa botga xush kelibsiz!");
  } else if (user.is_banned) {
    await sendMessage(userId, "🚫 Siz botdan bloklangansiz.");
    return;
  }

  const subscribed = await checkSubscription(userId);
  if (!subscribed) {
    const channels = await getChannels();
    const reqChannels = channels.filter(ch => ch.channel_type !== 'url');
    if (reqChannels.length > 0) {
      let text = "❗ Botdan foydalanish uchun quyidagi kanallarga a'zo bo'ling:\n\n";
      for (const ch of reqChannels) {
        text += `• ${ch.channel_name || ch.channel_username}\n`;
      }
      text += "\nA'zo bo'lgandan keyin: /start";
      await sendMessage(userId, text, undefined, undefined);
      return;
    }
  }

  await sendMessage(userId, `👋 Assalomu alaykum, ${firstName}!`, mainMenu());
}

async function checkSubscription(userId: number): Promise<boolean> {
  const channels = await getChannels();
  const reqChannels = channels.filter(ch => ch.channel_type !== 'url');
  for (const ch of reqChannels) {
    try {
      const res = await tgApi('getChatMember', { chat_id: ch.channel_id, user_id: userId });
      const status = res?.result?.status;
      if (status !== 'member' && status !== 'administrator' && status !== 'creator') {
        return false;
      }
    } catch (e) {
    }
  }
  return true;
}

async function handleAdmin(userId: number, callbackData: string): Promise<void> {
  const admins = await getAdmins();
  if (!admins.includes(userId)) return;

  if (callbackData === 'anime_upload') {
    const nextCode = await getNextCode();
    await setState(userId, 'waiting_name', { code: nextCode });
    await sendMessage(userId, `🔢 Auto kod: ${nextCode}\n\n📝 Manhwa nomini kiriting:`, cancelAdmin());
  }
}

async function handleCallback(userId: number, callbackData: string, messageText?: string): Promise<void> {
  const admins = await getAdmins();
  const isAdmin = admins.includes(userId);

  if (callbackData === 'main_menu') {
    await clearState(userId);
    await sendMessage(userId, "🏠 Bosh menyu", mainMenu());
    return;
  }

  if (callbackData === 'admin_panel' && isAdmin) {
    await clearState(userId);
    await sendMessage(userId, "🔧 Admin paneli", adminMenu());
    return;
  }

  if (callbackData === 'admin_channels' && isAdmin) {
    await clearState(userId);
    await sendMessage(userId, "📡 Kanal boshqaruvi:", channelsMenu());
    return;
  }

  if (callbackData === 'ch_required' && isAdmin) {
    await sendMessage(userId, "🔐 Majburiy obuna kanallar:", requiredChannels());
    return;
  }

  if (callbackData === 'ch_url' && isAdmin) {
    await sendMessage(userId, "🌐 Oddiy havola kanallar:", urlChannels());
    return;
  }

  if (callbackData.startsWith('ch_type:') && isAdmin) {
    const chType = callbackData.split(':')[1];
    const state = await getState(userId);
    const data = state?.data || {};
    data.ch_type = chType;

    if (chType === 'url') {
      await setState(userId, 'waiting_url', data);
      await sendMessage(userId, "🔗 Havolani kiriting:\n\nMasalan: https://site.com yoki https://t.me/kanal", cancelAdmin());
    } else {
      await setState(userId, 'waiting_channel_method', data);
      await sendMessage(userId, "📢 Kanal ulash usulini tanlang:", {
        inline_keyboard: [
          [{ text: "🆔 ID orqali", callback_data: "ch_method:id" }],
          [{ text: "🔗 Havola orqali", callback_data: "ch_method:link" }],
          [{ text: "📨 Postni forward qiling", callback_data: "ch_method:post" }],
          [{ text: "◀️ Orqaga", callback_data: "ch_required" }]
        ]
      });
    }
    return;
  }

  if (callbackData.startsWith('ch_method:') && isAdmin) {
    const method = callbackData.split(':')[1];
    const state = await getState(userId);
    const data = state?.data || {};
    data.ch_method = method;

    if (method === 'id') {
      await setState(userId, 'waiting_channel_id', data);
      await sendMessage(userId, "🆔 Kanal yoki guruh ID sini kiriting:\n\nID odatda -100... shaklida bo'ladi.", cancelAdmin());
    } else if (method === 'link') {
      await setState(userId, 'waiting_channel_link', data);
      await sendMessage(userId, "🔗 Kanal/guruh havolasini yuboring:\n\nMasalan: @kanal_nomi yoki https://t.me/kanal", cancelAdmin());
    }
    return;
  }

  if (callbackData === 'url_ch_list' && isAdmin) {
    const channels = await getChannels();
    const urlChannels = channels.filter(ch => ch.channel_type === 'url');
    if (urlChannels.length === 0) {
      await sendMessage(userId, "📋 Oddiy havola kanallar ro'yxati bo'sh.", backAdmin('ch_url'));
      return;
    }
    let text = "📋 Oddiy havola kanallar:\n\n";
    const kb = { inline_keyboard: [] as any };
    for (const ch of urlChannels) {
      text += `• ${ch.channel_name}\n`;
      kb.inline_keyboard.push([{ text: `🗑 ${ch.channel_name}`, callback_data: `url_ch_del:${ch.id}` }]);
    }
    kb.inline_keyboard.push([{ text: "◀️ Orqaga", callback_data: "ch_url" }]);
    await sendMessage(userId, text, kb);
    return;
  }

  if (callbackData.startsWith('url_ch_del:') && isAdmin) {
    const id = parseInt(callbackData.split(':')[2]);
    await deleteChannelById(id);
    await sendMessage(userId, "✅ Kanal o'chirildi.", backAdmin('url_ch_list'));
    return;
  }
}

async function handleMessage(userId: number, text: string | undefined, message: any): Promise<void> {
  const admins = await getAdmins();
  const isAdmin = admins.includes(userId);
  const state = await getState(userId);

  if (text === '/start') {
    await handleStart(userId, message.from.username, message.from.first_name, message.from.last_name);
    return;
  }

  if (text === '/admin' && isAdmin) {
    await sendMessage(userId, "🔧 Admin paneli", adminMenu());
    return;
  }

  if (state && isAdmin) {
    const data = state.data;
    if (state.state === 'waiting_name') {
      data.name = text;
      await setState(userId, 'waiting_genre', data);
      await sendMessage(userId, "🎭 Manhwa janrini kiriting:\n\n/skip - o'tkazib yuborish", skipKb('skip_genre'));
    } else if (state.state === 'waiting_genre') {
      data.genre = text;
      await setState(userId, 'waiting_studio', data);
      await sendMessage(userId, "🎙 Ovoz bergan studiya:\\n\\n/skip - o'tkazib yuborish", skipKb('skip_studio'));
    } else if (state.state === 'waiting_studio') {
      data.studio = text;
      await setState(userId, 'waiting_poster', data);
      await sendMessage(userId, "🎬 Posterni yuboring (Rasm/Video).", cancelAdmin());
    } else if (state.state === 'waiting_poster') {
      let fileId = null;
      if (message.photo) fileId = message.photo[message.photo.length - 1].file_id;
      else if (message.video) fileId = message.video.file_id;
      else if (message.animation) fileId = message.animation.file_id;

      if (fileId) {
        await addAnime(data.code, data.name, data.genre, data.studio, fileId);
        await setState(userId, 'waiting_episodes', { code: data.code, count: 0 });
        await sendMessage(userId, "✅ Manhwa saqlandi!\n\n📤 Endi boblarni yuboring (video yoki PDF).\nTugatgach: /done deb yozing.", cancelAdmin());
      } else {
        await sendMessage(userId, "❌ Rasm yoki video yuboring!", cancelAdmin());
      }
    } else if (state.state === 'waiting_episodes') {
      if (text === '/done') {
        const code = data.code;
        const anime = await getAnime(code);
        await clearState(userId);
        await sendMessage(userId, `✅ Manhwa saqlandi!\n📌 Kod: ${code}\n📺 Nomi: ${anime?.name}\n📦 Jami: ${data.count} bob.`, backAdmin());
      } else {
        let fileId = null;
        let fileType = '';
        let fileName = '';

        if (message.video) {
          fileId = message.video.file_id;
          fileType = 'video';
        } else if (message.document) {
          fileId = message.document.file_id;
          fileType = 'document';
          fileName = message.document.file_name;
        }

        if (fileId) {
          data.count++;
          await addEpisode(data.code, 1, data.count, fileId, fileType, fileName);
          await setState(userId, 'waiting_episodes', data);
        }
      }
    } else if (state.state === 'waiting_url') {
      await addChannel('', '', 'URL Kanal', 'url', text);
      await clearState(userId);
      await sendMessage(userId, "✅ Oddiy havola kanali qo'shildi.", backAdmin('ch_url'));
    }
  }
}

export default {
  async fetch(request: Request, env: any, ctx: ExecutionContext): Promise<Response> {
    (globalThis as any).__env__ = env;
    (globalThis as any).DB = env.DB;
    (globalThis as any).STATE = env.STATE;

    const url = new URL(request.url);

    if (url.pathname === `/webhook/${WEBHOOK_SECRET}` && request.method === 'POST') {
      try {
        const update = await request.json() as any;

        if (update.message) {
          await handleMessage(update.message.from.id, update.message.text, update.message);
        } else if (update.callback_query) {
          await handleCallback(update.callback_query.from.id, update.callback_query.data, update.callback_query.message.text);
          await tgApi('answerCallbackQuery', { callback_query_id: update.callback_query.id });
        }

        return new Response('OK', { status: 200 });
      } catch (e) {
        console.error(e);
        return new Response('Error', { status: 500 });
      }
    }

    return new Response('Not Found', { status: 404 });
  }
};
