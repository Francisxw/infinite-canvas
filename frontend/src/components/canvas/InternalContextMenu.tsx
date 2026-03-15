import {
  DefaultContextMenu,
  TldrawUiMenuActionItem,
  TldrawUiMenuGroup,
  TldrawUiMenuItem,
  TldrawUiMenuSubmenu,
  type TLUiContextMenuProps,
  useEditor,
} from 'tldraw'

type NodeType = 'text-node' | 'image-node' | 'video-node' | 'ai-prompt-node'

function AddNodeSubmenu() {
  const editor = useEditor()

  const createNode = (type: NodeType) => {
    const screen = editor.inputs.currentScreenPoint
    const page = editor.screenToPage(screen)
    editor.createShape({
      type,
      x: page.x - 180,
      y: page.y - 120,
    })
    editor.setCurrentTool('select')
  }

  return (
    <TldrawUiMenuSubmenu id="add-node" label="添加节点" size="small">
      <TldrawUiMenuGroup id="add-node-group">
        <TldrawUiMenuItem id="add-node-text" label="添加文本节点" onSelect={() => createNode('text-node')} />
        <TldrawUiMenuItem id="add-node-image" label="添加图片节点" onSelect={() => createNode('image-node')} />
        <TldrawUiMenuItem id="add-node-video" label="添加视频节点" onSelect={() => createNode('video-node')} />
        <TldrawUiMenuItem id="add-node-ai" label="添加提示节点" onSelect={() => createNode('ai-prompt-node')} />
      </TldrawUiMenuGroup>
    </TldrawUiMenuSubmenu>
  )
}

export function InternalContextMenu(props: TLUiContextMenuProps) {
  return (
    <DefaultContextMenu {...props}>
      <TldrawUiMenuGroup id="clipboard-core">
        <TldrawUiMenuActionItem actionId="paste" />
      </TldrawUiMenuGroup>

      <TldrawUiMenuGroup id="copy-export-core">
        <TldrawUiMenuSubmenu id="copy-as" label="复制为" size="small">
          <TldrawUiMenuGroup id="copy-as-group">
            <TldrawUiMenuActionItem actionId="copy-as-png" />
            <TldrawUiMenuActionItem actionId="copy-as-svg" />
          </TldrawUiMenuGroup>
        </TldrawUiMenuSubmenu>

        <TldrawUiMenuSubmenu id="export-as" label="导出为" size="small">
          <TldrawUiMenuGroup id="export-as-group">
            <TldrawUiMenuActionItem actionId="export-as-png" />
            <TldrawUiMenuActionItem actionId="export-as-svg" />
          </TldrawUiMenuGroup>
        </TldrawUiMenuSubmenu>
      </TldrawUiMenuGroup>

      <TldrawUiMenuGroup id="select-all-core">
        <TldrawUiMenuActionItem actionId="select-all" />
      </TldrawUiMenuGroup>

      <TldrawUiMenuGroup id="add-node-core">
        <AddNodeSubmenu />
      </TldrawUiMenuGroup>
    </DefaultContextMenu>
  )
}
