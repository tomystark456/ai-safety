const stories = [
  {
    id: "city-budget",
    cat: "news",
    lead: true,
    title: "Городской бюджет на следующий год вынесли на публичное обсуждение",
    time: "Сегодня 18:10",
    body: "Макетная заметка. Акимат опубликовал проект расходов и собирает замечания жителей до конца месяца. В документе отдельно выделены ремонт дворов, освещение и общественный транспорт.",
    image: "img/city-budget.jpg"
  },
  {
    id: "river",
    cat: "news",
    title: "На набережной открыли новую пешеходную зону",
    time: "Сегодня 16:40",
    body: "Макетная заметка. Зона рассчитана на прогулки и ярмарку выходного дня. Движение машин по соседней улице на время работ сделали односторонним.",
    image: "img/river.jpg"
  },
  {
    id: "school",
    cat: "news",
    title: "Школы перешли на зимнее расписание кружков",
    time: "Сегодня 15:05",
    body: "Макетная заметка. Секции заканчиваются раньше, чтобы дети успевали домой до темноты. Расписание вывесили на сайтах школ.",
    image: "img/school.jpg"
  },
  {
    id: "market",
    cat: "life",
    title: "На выходных в парке пройдёт книжная ярмарка",
    time: "Сегодня 14:20",
    body: "Макетная заметка. Будут местные издательства и читка коротких рассказов. Вход свободный.",
    image: "img/market.jpg"
  },
  {
    id: "cafe",
    cat: "life",
    title: "В центре открылась кофейня с мастерскими по выходным",
    time: "Сегодня 12:11",
    body: "Макетная заметка. По субботам там учат заваривать фильтр-кофе. Мест немного, запись на стойке.",
    image: "img/cafe.jpg"
  },
  {
    id: "match",
    cat: "sport",
    title: "Городская команда сыграет дома в субботу",
    time: "Сегодня 13:48",
    body: "Макетная заметка. Начало в 17:00. Билеты продают на стадионе и онлайн.",
    image: "img/match.jpg"
  },
  {
    id: "run",
    cat: "sport",
    title: "Любительский забег на 5 километров перенесли из-за ветра",
    time: "Сегодня 11:02",
    body: "Макетная заметка. Новый старт назначен на воскресенье, маршрут тот же.",
    image: "img/run.jpg"
  },
  {
    id: "road",
    cat: "auto",
    title: "На выезде из города сузят одну полосу на две недели",
    time: "Сегодня 10:30",
    body: "Макетная заметка. Причина — замена ограждения. Водителям советуют закладывать дополнительные двадцать минут.",
    image: "img/road.jpg"
  },
  {
    id: "bus",
    cat: "auto",
    title: "Ночной автобусный маршрут продлили до вокзала",
    time: "Вчера 19:15",
    body: "Макетная заметка. Рейсы ходят раз в час с 23:00 до 5:00.",
    image: "img/bus.jpg"
  },
  {
    id: "lake",
    cat: "travel",
    title: "К озеру пустили дополнительный утренний рейс",
    time: "Сегодня 09:40",
    body: "Макетная заметка. Автобус отправляется от центрального рынка в 7:20 по субботам и воскресеньям.",
    image: "img/lake.jpg"
  },
  {
    id: "pass",
    cat: "travel",
    title: "Горный перевал открыт, но рекомендованы цепи",
    time: "Сегодня 08:05",
    body: "Макетная заметка. Ночью прошёл мокрый снег. Днём обещают просвет.",
    image: "img/pass.jpg"
  }
];

const hero = document.querySelector("#hero");
const feed = document.querySelector("#feed");
const reader = document.querySelector("#reader");

function openStory(story) {
  document.querySelector("#reader-kicker").textContent = story.cat;
  document.querySelector("#reader-title").textContent = story.title;
  document.querySelector("#reader-when").textContent = story.time;
  document.querySelector("#reader-body").innerHTML = `<img src="${story.image}" alt=""><p>${story.body}</p><p>Это учебная страница. Спросите чат справа внизу — отвечает локальная модель vicuna:7b.</p>`;
  reader.hidden = false;
}

function card(story, lead) {
  const button = document.createElement("button");
  button.className = "card" + (lead ? " lead" : "");
  button.innerHTML = `<img src="${story.image}" alt=""><div class="text"><p class="kicker">${story.cat}</p><h3>${story.title}</h3><p class="when">${story.time}</p></div>`;
  button.addEventListener("click", () => openStory(story));
  return button;
}

const news = stories.filter((story) => story.cat === "news");
const lead = news[0];
hero.append(card(lead, true));
const stack = document.createElement("div");
stack.className = "stack";
news.slice(1).forEach((story) => stack.append(card(story, false)));
hero.append(stack);

document.querySelectorAll(".cards").forEach((box) => {
  stories
    .filter((story) => story.cat === box.dataset.cat)
    .forEach((story) => box.append(card(story, false)));
});

stories.forEach((story) => {
  const item = document.createElement("li");
  const button = document.createElement("button");
  button.innerHTML = `<img src="${story.image}" alt=""><span><strong>${story.title}</strong><span class="when">${story.time} · ${story.cat}</span></span>`;
  button.addEventListener("click", () => openStory(story));
  item.append(button);
  feed.append(item);
});

document.querySelector("#close-reader").addEventListener("click", () => {
  reader.hidden = true;
});
reader.addEventListener("click", (event) => {
  if (event.target === reader) reader.hidden = true;
});

const chat = document.querySelector("#chat");
const log = document.querySelector("#log");
const form = document.querySelector("#form");
const input = document.querySelector("#input");
const send = document.querySelector("#send");
const status = document.querySelector("#status");
const messages = [];

document.querySelector("#chat-fab").addEventListener("click", () => {
  chat.hidden = false;
  input.focus();
});
document.querySelector("#chat-close").addEventListener("click", () => {
  chat.hidden = true;
});

function addBubble(role, text) {
  const node = document.createElement("div");
  node.className = "bubble " + role;
  node.textContent = text;
  log.append(node);
  log.scrollTop = log.scrollHeight;
  return node;
}

input.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    form.requestSubmit();
  }
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const text = input.value.trim();
  if (!text || send.disabled) return;
  input.value = "";
  messages.push({ role: "user", content: text });
  addBubble("user", text);
  const pending = addBubble("assistant", "…");
  send.disabled = true;
  status.textContent = "Модель отвечает…";
  let answer = "";
  try {
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ messages })
    });
    if (!response.ok || !response.body) {
      const errText = await response.text();
      throw new Error(errText || response.statusText);
    }
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";
    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop() || "";
      for (const line of lines) {
        if (!line.trim()) continue;
        const packet = JSON.parse(line);
        if (packet.error) throw new Error(packet.error);
        const piece = packet.message && packet.message.content;
        if (piece) {
          answer += piece;
          pending.textContent = answer;
          log.scrollTop = log.scrollHeight;
        }
      }
    }
    if (!answer) pending.textContent = "(пустой ответ)";
    messages.push({ role: "assistant", content: answer });
    status.textContent = "Готово. Можно писать дальше.";
  } catch (error) {
    pending.textContent = "Не удалось получить ответ. Проверьте, что Ollama запущена.";
    status.textContent = String(error.message || error);
    messages.pop();
  } finally {
    send.disabled = false;
    input.focus();
  }
});
