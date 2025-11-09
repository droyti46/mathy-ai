frontend/
  src/
    app/                 # маршрутизация, ProtectedRoute
    components/          # UI-атомы: Button, TextInput, Markdown, CopyButton, MascotEyes, CloudField
    lib/
      api/               # axios, stream.ts, stream_delta.ts
      store/             # auth.store.ts (Zustand)
    pages/               # Auth, Main (Tabs: Tasks/Theory/Daily), Task (Solve/Teach)
    styles/              # tailwind токены, шрифты
    main.tsx             # React root
  vite.config.ts, tailwind.config.js, ...

