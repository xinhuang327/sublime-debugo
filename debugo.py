import sublime, sublime_plugin
import string
import os

breakpointText = '_ = "breakpoint"'
instrumentPkgsToken = "{{InstrumentPkgs}}"

class AddGoBreakpointCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		view = self.view
		filePath = view.file_name()
		if not filePath.endswith(".go"):
			return
		# Walk through each region in the selection
		for region in view.sel():
			# Only interested in empty regions, otherwise they may span multiple
			# lines, which doesn't make sense for this command.
			if region.empty():
				# Expand the region to the full line it resides on, excluding the newline
				line = view.line(region)
				prevLine = view.line(line.begin()-1)
				prevLineContents = view.substr(prevLine)
				prevLinetextContent = prevLineContents.lstrip(string.whitespace)
				lineContents = view.substr(line)
				textContent = lineContents.lstrip(string.whitespace)
				if prevLinetextContent == breakpointText:
					# remove previous breakpoint
					prevLine.b = prevLine.b+1
					view.erase(edit, prevLine)
					removeMark(self.view, prevLine)
				elif textContent == breakpointText:
					line.b = line.b+1
					view.erase(edit, line)
					removeMark(self.view, line)
				else:
					# add breakpoint line before current line
					newLineContent = lineContents.replace(textContent, breakpointText+"\n")
					# Add the text at the beginning of the line
					view.insert(edit, line.begin(), newLineContent)
					addMark(self.view, line)

pkgsSet = set()
filesSet = set()
marksSet = set()

def addMark(view, line):
	key = "mark"+str(line.begin())
	view.add_regions(key, [line], "mark", "circle", sublime.HIDDEN | sublime.PERSISTENT)
	marksSet.add(key)

def removeMark(view, line):
	key = "mark"+str(line.begin())
	view.erase_regions(key)
	if key in marksSet:
		marksSet.remove(key)

def clearMarks(view):
	for key in marksSet:
		view.erase_regions(key)
	marksSet.clear()

def updateBreakpointInfo(view):
	filePath = view.file_name()
	if not filePath.endswith(".go"):
		return
	bpRegions = view.find_all(breakpointText)
	pkgPath = getPkgPathForFile(filePath)
	clearMarks(view)
	if len(bpRegions) == 0:
		# remove from breakpoint file list
		print(filePath, "no breakpoint found")
		if pkgPath in pkgsSet:
			pkgsSet.remove(pkgPath)
		if filePath in filesSet:
			filesSet.remove(filePath)
	else:
		# add to breakpoint file list
		print(filePath, "has breakpoint")
		pkgsSet.add(pkgPath)
		filesSet.add(filePath)
		for region in bpRegions:
			line = view.line(region)
			addMark(view, line)

	print("pkgsSet", pkgsSet)
	print("filesSet", filesSet)

def getPkgPathForFile(filePath):
	prefix = "github.com"
	idx = filePath.index(prefix)
	subPath = filePath[idx:]
	ridx = subPath.rindex(os.sep)
	pkgPath = subPath[:ridx]
	return pkgPath.replace(os.sep,"/") #returns github.com/.../pkgname

buildFileName = "xinhuang327_web_musictree_web.sublime-build"

class EventDump(sublime_plugin.EventListener):
	def on_load(self, view):
		updateBreakpointInfo(view)

	def on_pre_save(self, view):
		updateBreakpointInfo(view)

	def on_post_save(self, view):
		if not view.file_name().endswith(".go"):
			return
		instrumentPart = ""
		if len(pkgsSet) > 0:
			instrumentPart = "-instrument " + ",".join(list(pkgsSet))
		buildFilePath = os.path.join(sublime.packages_path(), "User\\"+buildFileName)
		f = open(buildFilePath, 'w')
		f.write(buildFileTemplate.replace(instrumentPkgsToken, instrumentPart))
		f.close()
 
buildFileTemplate = """{
	"shell_cmd": "echo Kill running process... &taskkill /F /FI \\\"WindowTitle eq Run Release\\\" /T & echo BUILDING Release... & go build & echo DONE & start \\\"Run Release\\\" cmd /c \\\"web.exe & pause\\\"",
	"working_dir": "${project_path:${folder}}\\\\..\\\\music_tree\\\\web",

	"variants": [
		{   
			"shell_cmd": "echo Kill running process... &taskkill /F /FI \\\"WindowTitle eq Run Debug\\\" /T & echo BUILDING Debug... & godebug build {{InstrumentPkgs}} main.go & echo DONE & start \\\"Run Debug\\\" cmd /c \\\"main.debug & pause\\\"",
			"shell": true,
			"name": "Build And Run Debug"
		},
		{   
			"shell_cmd": "echo BUILDING Release... & go build & echo DONE",
			"shell": true,
			"name": "Build Release"
		},
		{   
			"name": "- - - - - - - - -"
		},
		{   
			"shell_cmd": "echo Kill running process... &taskkill /F /FI \\\"WindowTitle eq Run Debug\\\" /T & start \\\"Run Debug\\\" cmd /c \\\"main.debug & pause\\\"",
			"shell": true,
			"name": "Run Debug"
		},
		{   
			"shell_cmd": "start \\\"Run Release\\\" cmd /c \\\"web.exe & pause\\\"",
			"shell": true,
			"name": "Run Release"
		}
	]
}"""