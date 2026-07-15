export function serialColumnDrawCallback() {
  return function drawCallback() {
    const api = this.api()
    const pageInfo = api.page.info()
    api
      .column(0, { search: 'applied', order: 'applied', page: 'current' })
      .nodes()
      .each((cell, i) => {
        cell.innerHTML = pageInfo.start + i + 1
      })
  }
}
