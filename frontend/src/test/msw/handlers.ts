import { http, HttpResponse } from 'msw'

const API = 'http://localhost:8000'

export const handlers = [
  // GET /v1/user/spaces
  http.get(`${API}/v1/user/spaces`, () => {
    return HttpResponse.json({
      spaces: ['public', 'me@example.com/private-a', 'org1/space-b'],
    })
  }),

  // GET /v1/search
  http.get(`${API}/v1/search`, ({ request }) => {
    const url = new URL(request.url)
    const q = url.searchParams.get('q') || ''
    const results = q
      ? [
          {
            id: '1',
            title: `Match for ${q}`,
            snippet: `${q} alpha beta`,
            score: 0.9,
            download_url: '',
          },
        ]
      : []
    return HttpResponse.json({ results })
  }),
]
