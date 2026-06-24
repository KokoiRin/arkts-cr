@Entry
@Component
struct SamplePage {
  private title: string = 'Hello'

  aboutToAppear() {
    this.title = 'Ready'
  }

  private helper(value: string): string {
    return value.trim()
  }

  build() {
    Column() {
      Text(this.helper(this.title))
    }
  }
}

export function formatName(name: string): string {
  return name.trim()
}
