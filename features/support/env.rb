require "fileutils"

PYTHON_TEST_VERSION = ENV.fetch("PYTHON_TEST_VERSION")

def current_ip
  return "host.docker.internal" if OS.mac?

  ip_addr = `ifconfig | grep -Eo 'inet (addr:)?([0-9]*\\\.){3}[0-9]*' | grep -v '127.0.0.1'`
  ip_list = /((?:[0-9]*\.){3}[0-9]*)/.match(ip_addr)
  ip_list.captures.first
end

Maze.hooks.before_all do
  # log to console, not the filesystem
  Maze.config.file_log = false
  Maze.config.log_requests = true

  # don't wait so long for requests/not to receive requests
  Maze.config.receive_requests_wait = 10
  Maze.config.receive_no_requests_wait = 10

  # warn if a test takes more than 5 seconds to send a request
  Maze.config.receive_requests_slow_threshold = 5

  # bugsnag-python doesn't need to send the integrity header
  Maze.config.enforce_bugsnag_integrity = false

  # install bugsnag into each fixture
  Dir.each_child("features/fixtures") do |path|
    fixture_directory = "#{Dir.pwd}/features/fixtures/#{path}"

    next unless File.directory?(fixture_directory)

    destination = "#{fixture_directory}/temp-bugsnag-python"

    FileUtils.mkdir(destination) unless File.exist?(destination)

    FileUtils.cp_r(
      ["bugsnag", "setup.py"],
      destination,
      remove_destination: true # delete destination before copying
    )

    at_exit do
      FileUtils.rm_rf(destination)
    end
  end
end

Maze.hooks.before do
  Maze::Runner.environment["BUGSNAG_API_KEY"] = $api_key
  Maze::Runner.environment["BUGSNAG_ERROR_ENDPOINT"] = "http://#{current_ip}:#{Maze.config.port}/notify"
  Maze::Runner.environment["BUGSNAG_SESSION_ENDPOINT"] = "http://#{current_ip}:#{Maze.config.port}/sessions"
end

5.upto(100) do |minor_version|
  Before("@not-python-3.#{minor_version}") do
    skip_this_scenario if PYTHON_TEST_VERSION == "3.#{minor_version}"
  end
end
