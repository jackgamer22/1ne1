#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdbool.h>
#include <pthread.h>
#include <unistd.h>
#include <errno.h>
#include <signal.h>
#include <time.h>
#include <sys/stat.h>
#include <sys/types.h>

#ifdef _WIN32
    #include <winsock2.h>
    #include <ws2tcpip.h>
    #include <direct.h>
    #define mkdir(path, mode) _mkdir(path)
    #define sleep(sec) Sleep((sec) * 1000)
    #pragma comment(lib, "ws2_32.lib")
#else
    #include <sys/socket.h>
    #include <netdb.h>
    #include <arpa/inet.h>
#endif

#define MAX_EMAIL_LENGTH 256
#define MAX_DOMAIN_LENGTH 128
#define MAX_LINE_LENGTH 512
#define NUM_THREADS 10
#define MAX_PROVIDERS 200

// ANSI Colors
#define RESET   "\033[0m"
#define BOLD    "\033[1m"
#define CYAN    "\033[36m"
#define GREEN   "\033[32m"
#define RED     "\033[31m"
#define YELLOW  "\033[33m"
#define BLUE    "\033[34m"
#define CLEAR   "\033[H\033[J"

// Configuration
#define DEFAULT_INPUT_FILE "emails.txt"
#define DEFAULT_OUTPUT_FOLDER "output"

// Mutex for thread safety
pthread_mutex_t stats_mutex = PTHREAD_MUTEX_INITIALIZER;

// Global variables for pause/resume/stop
volatile sig_atomic_t running = 1;
volatile sig_atomic_t paused = 0;

// Global statistics
long total_emails = 0;
long total_processed = 0;
long total_valid = 0;
long total_invalid = 0;
long thread_positions[NUM_THREADS];

// Structure for thread arguments
typedef struct {
    char input_file[256];
    char output_folder[256];
    long start_pos;
    long end_pos;
    int thread_id;
} ThreadArgs;

// Structure to hold provider information
typedef struct {
    char name[64];
    int count;
} ProviderInfo;

ProviderInfo providers[MAX_PROVIDERS];
int provider_count = 0;

// Function to handle signals (pause, resume, stop)
void signal_handler(int signo) {
    if (signo == SIGINT) {
        running = 0;
    }
#ifndef _WIN32
    else if (signo == SIGUSR1) {
        paused = 1;
    } else if (signo == SIGUSR2) {
        paused = 0;
    }
#endif
}

// Function to check email syntax
bool check_syntax(const char *email) {
    const char *at = strchr(email, '@');
    if (at == NULL || at == email || *(at + 1) == '\0') return false;
    if (strchr(at + 1, '.') == NULL) return false;
    return true;
}

// Function to check DNS records and SMTP connection
bool verify_email(const char *email) {
    char domain[MAX_DOMAIN_LENGTH];
    const char *at = strchr(email, '@');
    if (at == NULL) return false;
    strncpy(domain, at + 1, MAX_DOMAIN_LENGTH - 1);
    domain[MAX_DOMAIN_LENGTH - 1] = '\0';

    struct addrinfo hints, *res;
    memset(&hints, 0, sizeof(hints));
    hints.ai_family = AF_INET;
    hints.ai_socktype = SOCK_STREAM;

    if (getaddrinfo(domain, "25", &hints, &res) != 0) {
        return false;
    }

    bool success = false;
    int sock = (int)socket(res->ai_family, res->ai_socktype, res->ai_protocol);
    if (sock >= 0) {
        struct timeval tv;
        tv.tv_sec = 2;
        tv.tv_usec = 0;
#ifdef _WIN32
        DWORD timeout = 2000;
        setsockopt(sock, SOL_SOCKET, SO_SNDTIMEO, (const char*)&timeout, sizeof timeout);
        setsockopt(sock, SOL_SOCKET, SO_RCVTIMEO, (const char*)&timeout, sizeof timeout);
#else
        setsockopt(sock, SOL_SOCKET, SO_SNDTIMEO, (const char*)&tv, sizeof tv);
        setsockopt(sock, SOL_SOCKET, SO_RCVTIMEO, (const char*)&tv, sizeof tv);
#endif

        if (connect(sock, res->ai_addr, (int)res->ai_addrlen) == 0) {
            success = true;
        }
#ifdef _WIN32
        closesocket(sock);
#else
        close(sock);
#endif
    }

    freeaddrinfo(res);
    return success;
}

// Function to detect provider (Extensive list restored)
const char* detect_provider(const char *email) {
    char domain[MAX_DOMAIN_LENGTH];
    const char *at = strchr(email, '@');
    if (at == NULL) return "Unknown";
    strncpy(domain, at + 1, MAX_DOMAIN_LENGTH - 1);
    domain[MAX_DOMAIN_LENGTH - 1] = '\0';

    // --- Security Providers ---
    if (strstr(domain, "messagelabs")) return "MessageLabs";
    if (strstr(domain, "mimecast")) return "Mimecast";
    if (strstr(domain, "pphosted")) return "Proofpoint";
    if (strstr(domain, "barracuda")) return "Barracuda";
    if (strstr(domain, "sophos")) return "Sophos";
    if (strstr(domain, "trendmicro")) return "TrendMicro";

    // --- Regional & Branded ISPs ---
    if (strstr(domain, "comcast")) return "Comcast";
    if (strstr(domain, "charter")) return "Charter";
    if (strstr(domain, "cox.net")) return "Cox";
    if (strstr(domain, "sky.com")) return "Sky";
    if (strstr(domain, "bt.prod.cloud.openwave.ai")) return "BT";
    if (strstr(domain, "virginmedia")) return "VirginMedia";
    if (strstr(domain, "talktalk")) return "TalkTalk";
    if (strstr(domain, "earthlink")) return "Earthlink";
    if (strstr(domain, "windstream")) return "Windstream";
    if (strstr(domain, "orange.fr") || strstr(domain, "wanadoo.fr")) return "Orange";
    if (strstr(domain, "free.fr")) return "Free.fr";
    if (strstr(domain, "libero.it")) return "Libero";
    if (strstr(domain, "virgilio.it")) return "Virgilio";
    if (strstr(domain, "tiscali.it")) return "Tiscali";
    if (strstr(domain, "seznam.cz")) return "Seznam";
    if (strstr(domain, "t-online.de")) return "T-online";
    if (strstr(domain, "swisscom")) return "Swisscom";
    if (strstr(domain, "bluenet.ch")) return "Bluewin";
    if (strstr(domain, "post.ch")) return "SwissPost";
    if (strstr(domain, "biglobe.ne.jp")) return "Biglobe";
    if (strstr(domain, "so-net.ne.jp")) return "So-net";
    if (strstr(domain, "rakuten")) return "Rakuten";
    if (strstr(domain, "uol.com.br") || strstr(domain, "bol.com.br")) return "UOL";
    if (strstr(domain, "terra.com.br")) return "Terra";
    if (strstr(domain, "telstra")) return "Telstra";
    if (strstr(domain, "optusnet")) return "Optus";
    if (strstr(domain, "rogers.com")) return "Rogers";
    if (strstr(domain, "shaw.ca")) return "Shaw";

    // --- Specific Hosting Providers ---
    if (strstr(domain, "secureserver.net")) return "GoDaddy";
    if (strstr(domain, "emailsrvr.com")) return "Rackspace";
    if (strstr(domain, "1and1")) return "IONOS";
    if (strstr(domain, "hostgator")) return "HostGator";
    if (strstr(domain, "bluehost")) return "Bluehost";
    if (strstr(domain, "siteground")) return "SiteGround";
    if (strstr(domain, "privateemail.com")) return "NameCheap";
    if (strstr(domain, "networksolutions")) return "NetworkSolutions";
    if (strstr(domain, "ovh.net")) return "OVH";
    if (strstr(domain, "one.com")) return "One.com";

    // --- Major Global Providers ---
    if (strstr(domain, "google") || strstr(domain, "gmail")) return "Gmail";
    if (strstr(domain, "icloud") || strstr(domain, "apple.com")) return "Apple";
    if (strstr(domain, "outlook.com") || strstr(domain, "hotmail.com") || strstr(domain, "live.com") || strstr(domain, "msn.com")) return "Office365";
    if (strstr(domain, "aol.com")) return "Aol";
    if (strstr(domain, "yahoo")) return "Yahoo";
    if (strstr(domain, "protonmail") || strstr(domain, "proton.me")) return "Protonmail";
    if (strstr(domain, "zoho")) return "Zoho";
    if (strstr(domain, "yandex")) return "Yandex";
    if (strstr(domain, "mail.ru")) return "Mail.ru";
    if (strstr(domain, "fastmail")) return "Fastmail";
    if (strstr(domain, "gmx")) return "GMX";
    if (strstr(domain, "web.de")) return "Web.de";
    if (strstr(domain, "mail.com")) return "Mail.com";

    // --- Chinese Providers ---
    if (strstr(domain, "qq.com")) return "QQ";
    if (strstr(domain, "netease") || strstr(domain, "163.com") || strstr(domain, "126.com")) return "Netease";
    if (strstr(domain, "aliyun")) return "Aliyun";
    if (strstr(domain, "sina")) return "Sina";
    if (strstr(domain, "naver.com")) return "Naver";

    // --- Generic Webmail ---
    if (strstr(domain, "zimbra")) return "Zimbra";
    if (strstr(domain, "roundcube")) return "Roundcube";
    if (strstr(domain, "webmail") || strstr(domain, "cpanel") || strstr(domain, "plesk")) return "Webmail";

    return "Unknown";
}

// Function to update stats
void update_stats(const char *provider, bool is_valid) {
    pthread_mutex_lock(&stats_mutex);
    total_processed++;
    if (is_valid) {
        total_valid++;
        int found = 0;
        for (int i = 0; i < provider_count; i++) {
            if (strcmp(providers[i].name, provider) == 0) {
                providers[i].count++;
                found = 1;
                break;
            }
        }
        if (!found && provider_count < MAX_PROVIDERS) {
            strncpy(providers[provider_count].name, provider, 63);
            providers[provider_count].name[63] = '\0';
            providers[provider_count].count = 1;
            provider_count++;
        }
    } else {
        total_invalid++;
    }
    pthread_mutex_unlock(&stats_mutex);
}

// Function to write to file with thread safety
void write_to_file(const char *filename, const char *email) {
    pthread_mutex_lock(&stats_mutex);
    FILE *fp = fopen(filename, "a");
    if (fp != NULL) {
        fprintf(fp, "%s\n", email);
        fclose(fp);
    }
    pthread_mutex_unlock(&stats_mutex);
}

// Thread function
void *process_email(void *arg) {
    ThreadArgs *args = (ThreadArgs*) arg;
    int thread_id = args->thread_id;
    FILE *fp = fopen(args->input_file, "r");
    if (fp == NULL) pthread_exit(NULL);

    fseek(fp, args->start_pos, SEEK_SET);
    char line[MAX_LINE_LENGTH];
    long current_pos = args->start_pos;

    if (args->start_pos != 0) {
        if (fgets(line, MAX_LINE_LENGTH, fp)) {
            current_pos = ftell(fp);
        }
    }

    while (running && current_pos < args->end_pos && fgets(line, MAX_LINE_LENGTH, fp) != NULL) {
        thread_positions[thread_id] = current_pos;
        while (paused && running) sleep(1);

        line[strcspn(line, "\r\n")] = 0;
        if (strlen(line) == 0) {
            current_pos = ftell(fp);
            continue;
        }

        bool is_valid = check_syntax(line) && verify_email(line);
        const char *provider = detect_provider(line);

        update_stats(provider, is_valid);

        char out_path[512];
        if (is_valid) {
            snprintf(out_path, sizeof(out_path), "%s/valid.txt", args->output_folder);
            write_to_file(out_path, line);
            snprintf(out_path, sizeof(out_path), "%s/%s.txt", args->output_folder, provider);
            write_to_file(out_path, line);
        } else {
            snprintf(out_path, sizeof(out_path), "%s/invalid.txt", args->output_folder);
            write_to_file(out_path, line);
        }
        current_pos = ftell(fp);
    }
    thread_positions[thread_id] = current_pos;
    fclose(fp);
    return NULL;
}

// Dashboard renderer
void *render_dashboard(void *arg) {
    long file_size = *(long*)arg;
    if (file_size == 0) file_size = 1;

    while (running) {
        long processed_bytes = 0;
        for (int i = 0; i < NUM_THREADS; i++) processed_bytes += thread_positions[i];

        double progress = (double)processed_bytes / (double)file_size * 100.0;
        if (progress > 100.0) progress = 100.0;

        printf(CLEAR);
        printf(BOLD CYAN "========================================================\n" RESET);
        printf(BOLD CYAN "            MAGXXICVOX ADVANCE EMAIL SORTER            \n" RESET);
        printf(BOLD CYAN "========================================================\n" RESET);
        printf(BOLD " Status:  " RESET);
        if (paused) printf(YELLOW "[PAUSED]  " RESET);
        else printf(GREEN "[RUNNING] " RESET);
        printf(" |  Threads: %d\n", NUM_THREADS);

        printf(BOLD " Progress: " RESET "[");
        int bar_width = 30;
        int pos = (int)(progress / 100.0 * bar_width);
        for (int i = 0; i < bar_width; i++) {
            if (i < pos) printf(GREEN "=" RESET);
            else if (i == pos) printf(GREEN ">" RESET);
            else printf(" ");
        }
        printf("] %.2f%%\n", progress);

        printf(BOLD CYAN "--------------------------------------------------------\n" RESET);
        printf(BOLD " STATISTICS:\n" RESET);
        printf(BOLD "  Processed: %-10ld" RESET " | " BOLD GREEN " Valid:   %-10ld\n" RESET, total_processed, total_valid);
        printf(BOLD "  Total:     %-10ld" RESET " | " BOLD RED " Invalid: %-10ld\n" RESET, total_emails, total_invalid);

        printf(BOLD CYAN "--------------------------------------------------------\n" RESET);
        printf(BOLD " PROVIDER BREAKDOWN:\n" RESET);
        for (int i = 0; i < provider_count && i < 20; i++) { // Show top 20
            printf("  %-15s: %-8d", providers[i].name, providers[i].count);
            if ((i + 1) % 2 == 0) printf("\n");
        }
        if (provider_count % 2 != 0) printf("\n");
        if (provider_count > 20) printf("  ... and %d more\n", provider_count - 20);
        printf(BOLD CYAN "========================================================\n" RESET);
#ifdef _WIN32
        printf(" [CTRL+C] Stop\n");
#else
        printf(" [CTRL+C] Stop | [SIGUSR1] Pause | [SIGUSR2] Resume\n");
#endif
        fflush(stdout);
        sleep(1);
    }
    return NULL;
}

int main(int argc, char *argv[]) {
#ifdef _WIN32
    WSADATA wsa;
    WSAStartup(MAKEWORD(2, 2), &wsa);
    signal(SIGINT, signal_handler);
#else
    struct sigaction sa;
    sa.sa_handler = signal_handler;
    sigemptyset(&sa.sa_mask);
    sa.sa_flags = 0;
    sigaction(SIGINT, &sa, NULL);
    sigaction(SIGUSR1, &sa, NULL);
    sigaction(SIGUSR2, &sa, NULL);
#endif

    char *input_file = (char*)DEFAULT_INPUT_FILE;
    char *output_folder = (char*)DEFAULT_OUTPUT_FOLDER;
    if (argc > 1) input_file = argv[1];
    if (argc > 2) output_folder = argv[2];

    struct stat st = {0};
    if (stat(output_folder, &st) == -1) mkdir(output_folder, 0777);

    FILE *fp = fopen(input_file, "r");
    if (fp == NULL) {
        perror("Error opening input file");
        return 1;
    }

    char line[MAX_LINE_LENGTH];
    while (fgets(line, MAX_LINE_LENGTH, fp)) total_emails++;
    fseek(fp, 0, SEEK_END);
    long file_size = ftell(fp);
    fclose(fp);

    for (int i = 0; i < NUM_THREADS; i++) thread_positions[i] = 0;
    long chunk_size = file_size / NUM_THREADS;

    pthread_t threads[NUM_THREADS], dash_thread;
    ThreadArgs args[NUM_THREADS];

    for (int i = 0; i < NUM_THREADS; i++) {
        args[i].thread_id = i;
        strncpy(args[i].input_file, input_file, 255);
        strncpy(args[i].output_folder, output_folder, 255);
        args[i].start_pos = i * chunk_size;
        args[i].end_pos = (i == NUM_THREADS - 1) ? file_size : (i + 1) * chunk_size;
        pthread_create(&threads[i], NULL, process_email, (void *)&args[i]);
    }

    pthread_create(&dash_thread, NULL, render_dashboard, (void*)&file_size);

    for (int i = 0; i < NUM_THREADS; i++) pthread_join(threads[i], NULL);
    running = 0;
    pthread_join(dash_thread, NULL);

    printf("\n" BOLD GREEN "Email sorting complete." RESET "\n");
#ifdef _WIN32
    WSACleanup();
#endif
    return 0;
}
